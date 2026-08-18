from datetime import date
import secrets

from sqlalchemy.orm import Session

from app.core.error import AppError, ErrorCode
from app.module.audit_log import AuditLogModule
from app.module.business_types import (
    MemberRole,
    OrderStatus,
    ReservationStatus,
    ShipmentStatus,
)
from app.module.sales_order import SalesOrderModule
from app.module.sales_order_item import SalesOrderItemModule
from app.module.shipment import Shipment, ShipmentModule
from app.module.shipment_item import ShipmentItemModule
from app.module.shipment_status_history import ShipmentStatusHistoryModule
from app.module.stock_reservation import StockReservationModule
from app.module.warehouse import WarehouseModule
from app.usecase.organizations._operations import RequireOrganizationRoleOperation


class CreateShipmentUsecase:
    def __init__(self, db: Session):
        self.db = db
        self.require_role = RequireOrganizationRoleOperation(db)
        self.orders = SalesOrderModule(db)
        self.order_items = SalesOrderItemModule(db)
        self.warehouses = WarehouseModule(db)
        self.reservations = StockReservationModule(db)
        self.shipments = ShipmentModule(db)
        self.shipment_items = ShipmentItemModule(db)
        self.history = ShipmentStatusHistoryModule(db)
        self.audit_logs = AuditLogModule(db)

    def execute(
        self,
        *,
        account_id: int,
        order_id: int,
        warehouse_id: int,
        note: str | None,
    ) -> Shipment:
        order = self.orders.get_for_update(order_id)
        if not order:
            raise AppError(code=ErrorCode.ORDER_NOT_FOUND)
        self.require_role.run(
            organization_id=order.seller_organization_id,
            account_id=account_id,
            allowed_roles={MemberRole.ADMIN.value, MemberRole.WAREHOUSE.value},
        )
        if order.status not in {
            OrderStatus.ALLOCATED.value,
            OrderStatus.PARTIALLY_ALLOCATED.value,
            OrderStatus.PARTIALLY_SHIPPED.value,
        }:
            raise AppError(code=ErrorCode.INVALID_ORDER_STATE)
        warehouse = self.warehouses.get_by_id(warehouse_id)
        if not warehouse or warehouse.organization_id != order.seller_organization_id:
            raise AppError(code=ErrorCode.WAREHOUSE_NOT_FOUND)
        if any(
            shipment.warehouse_id == warehouse_id
            and shipment.status != ShipmentStatus.CANCELED.value
            for shipment in self.shipments.list_by_order(order.id)
        ):
            raise AppError(code=ErrorCode.INVALID_SHIPMENT_STATE)

        order_items = self.order_items.list_by_order(order.id)
        reservations = [
            reservation
            for reservation in self.reservations.list_by_order_items(
                [item.id for item in order_items], ReservationStatus.ACTIVE.value
            )
            if reservation.warehouse_id == warehouse_id
        ]
        if not reservations:
            raise AppError(code=ErrorCode.INVENTORY_NOT_FOUND)

        shipment = self.shipments.create(
            shipment_number=_new_shipment_number(),
            order_id=order.id,
            warehouse_id=warehouse_id,
            status=ShipmentStatus.CONFIRMED.value,
            note=note,
            created_by_account_id=account_id,
        )
        for reservation in reservations:
            self.shipment_items.create(
                shipment_id=shipment.id,
                order_item_id=reservation.order_item_id,
                product_id=reservation.product_id,
                quantity=reservation.quantity,
            )
        self.history.create(
            shipment_id=shipment.id,
            from_status=None,
            to_status=ShipmentStatus.CONFIRMED.value,
            reason=None,
            changed_by_account_id=account_id,
        )
        self.audit_logs.record(
            actor_account_id=account_id,
            action="shipment.created",
            resource_type="shipment",
            resource_id=shipment.id,
            details={"order_id": order.id, "warehouse_id": warehouse_id},
        )
        self.db.commit()
        return shipment


def _new_shipment_number() -> str:
    return f"SH-{date.today():%Y%m%d}-{secrets.token_hex(3).upper()}"
