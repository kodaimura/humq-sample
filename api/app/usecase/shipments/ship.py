from sqlalchemy.orm import Session

from app.core.error import AppError, ErrorCode
from app.module.audit_log import AuditLogModule
from app.module.business_types import (
    InventoryEventType,
    MemberRole,
    OrderStatus,
    ReservationStatus,
    ShipmentStatus,
)
from app.module.inventory_balance import InventoryBalanceModule
from app.module.inventory_ledger import InventoryLedgerModule
from app.module.outbox_event import OutboxEventModule
from app.module.sales_order import SalesOrderModule
from app.module.sales_order_status_history import SalesOrderStatusHistoryModule
from app.module.shipment import Shipment, ShipmentModule
from app.module.shipment_item import ShipmentItemModule
from app.module.shipment_status_history import ShipmentStatusHistoryModule
from app.module.stock_reservation import StockReservationModule
from app.query.order_fulfillment import OrderFulfillmentQuery
from app.usecase.organizations.require_role import RequireOrganizationRoleUsecase


class ShipShipmentUsecase:
    def __init__(self, db: Session):
        self.db = db
        self.require_role = RequireOrganizationRoleUsecase(db)
        self.shipments = ShipmentModule(db)
        self.shipment_items = ShipmentItemModule(db)
        self.shipment_history = ShipmentStatusHistoryModule(db)
        self.orders = SalesOrderModule(db)
        self.order_history = SalesOrderStatusHistoryModule(db)
        self.reservations = StockReservationModule(db)
        self.balances = InventoryBalanceModule(db)
        self.ledger = InventoryLedgerModule(db)
        self.fulfillment = OrderFulfillmentQuery(db)
        self.outbox = OutboxEventModule(db)
        self.audit_logs = AuditLogModule(db)

    def execute(
        self, *, account_id: int, shipment_id: int, tracking_number: str | None
    ) -> Shipment:
        shipment = self.shipments.get_for_update(shipment_id)
        if not shipment:
            raise AppError(code=ErrorCode.SHIPMENT_NOT_FOUND)
        order = self.orders.get_for_update(shipment.order_id)
        if not order:
            raise AppError(code=ErrorCode.ORDER_NOT_FOUND)
        self.require_role.execute(
            organization_id=order.seller_organization_id,
            account_id=account_id,
            allowed_roles={MemberRole.ADMIN.value, MemberRole.WAREHOUSE.value},
        )
        if shipment.status != ShipmentStatus.CONFIRMED.value:
            raise AppError(code=ErrorCode.INVALID_SHIPMENT_STATE)

        for shipment_item in self.shipment_items.list_by_shipment(shipment.id):
            reservations = self.reservations.list_by_order_item(
                shipment_item.order_item_id
            )
            reservation = next(
                (
                    candidate
                    for candidate in reservations
                    if candidate.warehouse_id == shipment.warehouse_id
                    and candidate.status == ReservationStatus.ACTIVE.value
                ),
                None,
            )
            if not reservation or reservation.quantity != shipment_item.quantity:
                raise AppError(code=ErrorCode.INVALID_SHIPMENT_STATE)
            balance = self.balances.get_for_update(
                warehouse_id=shipment.warehouse_id,
                product_id=shipment_item.product_id,
            )
            if not balance or not self.balances.consume_reserved(
                balance, shipment_item.quantity
            ):
                raise AppError(code=ErrorCode.INVENTORY_INSUFFICIENT)
            self.reservations.set_status(
                reservation, ReservationStatus.CONSUMED.value
            )
            self.ledger.record(
                warehouse_id=shipment.warehouse_id,
                product_id=shipment_item.product_id,
                event_type=InventoryEventType.SHIPMENT.value,
                on_hand_delta=-shipment_item.quantity,
                reserved_delta=-shipment_item.quantity,
                on_hand_after=balance.on_hand_quantity,
                reserved_after=balance.reserved_quantity,
                reference_type="shipment",
                reference_id=shipment.id,
                actor_account_id=account_id,
            )

        previous_shipment_status = self.shipments.change_status(
            shipment,
            ShipmentStatus.SHIPPED.value,
            tracking_number=tracking_number,
        )
        self.shipment_history.create(
            shipment_id=shipment.id,
            from_status=previous_shipment_status,
            to_status=ShipmentStatus.SHIPPED.value,
            reason=None,
            changed_by_account_id=account_id,
        )
        ordered_quantity, shipped_quantity = self.fulfillment.quantities(order.id)
        next_order_status = (
            OrderStatus.SHIPPED.value
            if shipped_quantity >= ordered_quantity
            else OrderStatus.PARTIALLY_SHIPPED.value
        )
        previous_order_status = self.orders.change_status(order, next_order_status)
        self.order_history.create(
            order_id=order.id,
            from_status=previous_order_status,
            to_status=next_order_status,
            reason=None,
            changed_by_account_id=account_id,
        )
        self.outbox.enqueue(
            event_type="shipment.shipped",
            aggregate_type="shipment",
            aggregate_id=shipment.id,
            payload={
                "shipment_id": shipment.id,
                "shipment_number": shipment.shipment_number,
                "order_id": order.id,
                "tracking_number": tracking_number,
            },
        )
        self.audit_logs.record(
            actor_account_id=account_id,
            action="shipment.shipped",
            resource_type="shipment",
            resource_id=shipment.id,
            details={"tracking_number": tracking_number},
        )
        self.db.commit()
        return shipment
