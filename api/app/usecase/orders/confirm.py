from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.error import AppError, ErrorCode
from app.module.audit_log import AuditLogModule
from app.module.business_types import (
    InventoryEventType,
    MemberRole,
    OrderStatus,
    ReservationStatus,
)
from app.module.inventory_balance import InventoryBalanceModule
from app.module.inventory_ledger import InventoryLedgerModule
from app.module.outbox_event import OutboxEventModule
from app.module.sales_order import SalesOrder, SalesOrderModule
from app.module.sales_order_item import SalesOrderItemModule
from app.module.sales_order_status_history import SalesOrderStatusHistoryModule
from app.module.stock_reservation import StockReservationModule
from app.module.warehouse import WarehouseModule
from app.usecase.organizations._operations import RequireOrganizationRoleOperation


@dataclass(frozen=True)
class ConfirmOrderInput:
    account_id: int
    order_id: int


class ConfirmOrderUsecase:
    def __init__(self, db: Session):
        self.db = db
        self.require_role = RequireOrganizationRoleOperation(db)
        self.orders = SalesOrderModule(db)
        self.items = SalesOrderItemModule(db)
        self.warehouses = WarehouseModule(db)
        self.balances = InventoryBalanceModule(db)
        self.reservations = StockReservationModule(db)
        self.ledger = InventoryLedgerModule(db)
        self.history = SalesOrderStatusHistoryModule(db)
        self.outbox = OutboxEventModule(db)
        self.audit_logs = AuditLogModule(db)

    def execute(self, input: ConfirmOrderInput) -> SalesOrder:
        order = self.orders.get_for_update(input.order_id)
        if not order:
            raise AppError(code=ErrorCode.ORDER_NOT_FOUND)
        self.require_role.run(
            organization_id=order.seller_organization_id,
            account_id=input.account_id,
            allowed_roles={MemberRole.ADMIN.value, MemberRole.SALES.value},
        )
        if order.status != OrderStatus.DRAFT.value:
            raise AppError(code=ErrorCode.INVALID_ORDER_STATE)

        warehouses = [
            warehouse
            for warehouse in self.warehouses.list_by_organization(
                order.seller_organization_id
            )
            if warehouse.active
        ]
        ordered_quantity = 0
        reserved_quantity = 0
        for item in self.items.list_by_order(order.id):
            ordered_quantity += item.quantity
            remaining = item.quantity
            for warehouse in warehouses:
                balance = self.balances.get_for_update(
                    warehouse_id=warehouse.id, product_id=item.product_id
                )
                if not balance or balance.available_quantity <= 0:
                    continue
                quantity = min(balance.available_quantity, remaining)
                if not self.balances.reserve(balance, quantity):
                    continue
                reservation = self.reservations.create(
                    order_item_id=item.id,
                    warehouse_id=warehouse.id,
                    product_id=item.product_id,
                    quantity=quantity,
                )
                self.ledger.record(
                    warehouse_id=warehouse.id,
                    product_id=item.product_id,
                    event_type=InventoryEventType.RESERVATION.value,
                    on_hand_delta=0,
                    reserved_delta=quantity,
                    on_hand_after=balance.on_hand_quantity,
                    reserved_after=balance.reserved_quantity,
                    reference_type="stock_reservation",
                    reference_id=reservation.id,
                    actor_account_id=input.account_id,
                )
                reserved_quantity += quantity
                remaining -= quantity
                if remaining == 0:
                    break

        next_status = (
            OrderStatus.ALLOCATED.value
            if reserved_quantity == ordered_quantity
            else OrderStatus.PARTIALLY_ALLOCATED.value
        )
        previous = self.orders.change_status(order, next_status)
        self.history.create(
            order_id=order.id,
            from_status=previous,
            to_status=next_status,
            reason=None if reserved_quantity == ordered_quantity else "Insufficient stock",
            changed_by_account_id=input.account_id,
        )
        self.outbox.enqueue(
            event_type="order.confirmed",
            aggregate_type="sales_order",
            aggregate_id=order.id,
            payload={
                "order_id": order.id,
                "order_number": order.order_number,
                "status": next_status,
                "ordered_quantity": ordered_quantity,
                "reserved_quantity": reserved_quantity,
            },
        )
        self.audit_logs.record(
            actor_account_id=input.account_id,
            action="order.confirmed",
            resource_type="sales_order",
            resource_id=order.id,
            details={"reserved_quantity": reserved_quantity},
        )
        self.db.commit()
        return order
