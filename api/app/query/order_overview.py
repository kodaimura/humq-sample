from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.module.business_types import ReservationStatus, ShipmentStatus
from app.module.organization.model import Organization
from app.module.sales_order.model import SalesOrder
from app.module.sales_order_item.model import SalesOrderItem
from app.module.shipment.model import Shipment
from app.module.shipment_item.model import ShipmentItem
from app.module.stock_reservation.model import StockReservation


@dataclass(frozen=True)
class OrderOverview:
    id: int
    order_number: str
    customer_name: str
    status: str
    requested_ship_date: date | None
    total_amount: Decimal
    item_count: int
    ordered_quantity: int
    reserved_quantity: int
    shipped_quantity: int
    created_at: datetime


class OrderOverviewQuery:
    def __init__(self, db: Session):
        self.db = db

    def list_by_seller(self, seller_organization_id: int) -> list[OrderOverview]:
        item_totals = (
            select(
                SalesOrderItem.order_id.label("order_id"),
                func.count(SalesOrderItem.id).label("item_count"),
                func.sum(SalesOrderItem.quantity).label("ordered_quantity"),
            )
            .group_by(SalesOrderItem.order_id)
            .subquery()
        )
        reservation_totals = (
            select(
                SalesOrderItem.order_id.label("order_id"),
                func.sum(
                    case(
                        (
                            StockReservation.status == ReservationStatus.ACTIVE.value,
                            StockReservation.quantity,
                        ),
                        else_=0,
                    )
                ).label("reserved_quantity"),
            )
            .join(StockReservation, StockReservation.order_item_id == SalesOrderItem.id)
            .group_by(SalesOrderItem.order_id)
            .subquery()
        )
        shipped_totals = (
            select(
                Shipment.order_id.label("order_id"),
                func.sum(
                    case(
                        (
                            Shipment.status == ShipmentStatus.SHIPPED.value,
                            ShipmentItem.quantity,
                        ),
                        else_=0,
                    )
                ).label("shipped_quantity"),
            )
            .join(ShipmentItem, ShipmentItem.shipment_id == Shipment.id)
            .group_by(Shipment.order_id)
            .subquery()
        )
        stmt = (
            select(
                SalesOrder.id,
                SalesOrder.order_number,
                Organization.name.label("customer_name"),
                SalesOrder.status,
                SalesOrder.requested_ship_date,
                SalesOrder.total_amount,
                func.coalesce(item_totals.c.item_count, 0).label("item_count"),
                func.coalesce(item_totals.c.ordered_quantity, 0).label(
                    "ordered_quantity"
                ),
                func.coalesce(reservation_totals.c.reserved_quantity, 0).label(
                    "reserved_quantity"
                ),
                func.coalesce(shipped_totals.c.shipped_quantity, 0).label(
                    "shipped_quantity"
                ),
                SalesOrder.created_at,
            )
            .join(Organization, Organization.id == SalesOrder.customer_organization_id)
            .outerjoin(item_totals, item_totals.c.order_id == SalesOrder.id)
            .outerjoin(
                reservation_totals, reservation_totals.c.order_id == SalesOrder.id
            )
            .outerjoin(shipped_totals, shipped_totals.c.order_id == SalesOrder.id)
            .where(SalesOrder.seller_organization_id == seller_organization_id)
            .order_by(SalesOrder.id.desc())
        )
        return [OrderOverview(**row._mapping) for row in self.db.execute(stmt)]
