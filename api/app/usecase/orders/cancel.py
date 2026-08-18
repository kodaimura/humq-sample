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
from app.usecase.organizations._operations import RequireOrganizationRoleOperation


class CancelOrderUsecase:
    def __init__(self, db: Session):
        self.db = db
        self.require_role = RequireOrganizationRoleOperation(db)
        self.orders = SalesOrderModule(db)
        self.items = SalesOrderItemModule(db)
        self.reservations = StockReservationModule(db)
        self.balances = InventoryBalanceModule(db)
        self.ledger = InventoryLedgerModule(db)
        self.history = SalesOrderStatusHistoryModule(db)
        self.outbox = OutboxEventModule(db)
        self.audit_logs = AuditLogModule(db)

    def execute(
        self, *, account_id: int, order_id: int, reason: str | None
    ) -> SalesOrder:
        order = self.orders.get_for_update(order_id)
        if not order:
            raise AppError(code=ErrorCode.ORDER_NOT_FOUND)
        self.require_role.run(
            organization_id=order.seller_organization_id,
            account_id=account_id,
            allowed_roles={MemberRole.ADMIN.value, MemberRole.SALES.value},
        )
        if order.status not in {
            OrderStatus.DRAFT.value,
            OrderStatus.CONFIRMED.value,
            OrderStatus.PARTIALLY_ALLOCATED.value,
            OrderStatus.ALLOCATED.value,
        }:
            raise AppError(code=ErrorCode.INVALID_ORDER_STATE)
        order_items = self.items.list_by_order(order.id)
        active = self.reservations.list_by_order_items(
            [item.id for item in order_items], ReservationStatus.ACTIVE.value
        )
        for reservation in active:
            balance = self.balances.get_for_update(
                warehouse_id=reservation.warehouse_id,
                product_id=reservation.product_id,
            )
            if not balance or not self.balances.release(balance, reservation.quantity):
                raise AppError(code=ErrorCode.INVALID_ORDER_STATE)
            self.reservations.set_status(reservation, ReservationStatus.RELEASED.value)
            self.ledger.record(
                warehouse_id=reservation.warehouse_id,
                product_id=reservation.product_id,
                event_type=InventoryEventType.RESERVATION_RELEASED.value,
                on_hand_delta=0,
                reserved_delta=-reservation.quantity,
                on_hand_after=balance.on_hand_quantity,
                reserved_after=balance.reserved_quantity,
                reference_type="stock_reservation",
                reference_id=reservation.id,
                actor_account_id=account_id,
            )
        previous = self.orders.change_status(order, OrderStatus.CANCELED.value)
        self.history.create(
            order_id=order.id,
            from_status=previous,
            to_status=OrderStatus.CANCELED.value,
            reason=reason,
            changed_by_account_id=account_id,
        )
        self.outbox.enqueue(
            event_type="order.canceled",
            aggregate_type="sales_order",
            aggregate_id=order.id,
            payload={"order_id": order.id, "order_number": order.order_number},
        )
        self.audit_logs.record(
            actor_account_id=account_id,
            action="order.canceled",
            resource_type="sales_order",
            resource_id=order.id,
            details={"reason": reason},
        )
        self.db.commit()
        return order
