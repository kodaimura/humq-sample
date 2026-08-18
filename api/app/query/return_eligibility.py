from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.module.business_types import SalesReturnStatus, ShipmentStatus
from app.module.sales_order_item.model import SalesOrderItem
from app.module.sales_return.model import SalesReturn
from app.module.sales_return_item.model import SalesReturnItem
from app.module.shipment.model import Shipment
from app.module.shipment_item.model import ShipmentItem


@dataclass(frozen=True)
class ReturnableOrderItem:
    order_item_id: int
    product_id: int
    shipped_quantity: int
    already_requested_quantity: int
    returnable_quantity: int


class ReturnEligibilityQuery:
    def __init__(self, db: Session):
        self.db = db

    def for_order(self, order_id: int) -> list[ReturnableOrderItem]:
        shipped = (
            select(
                ShipmentItem.order_item_id.label("order_item_id"),
                func.sum(ShipmentItem.quantity).label("quantity"),
            )
            .join(Shipment, Shipment.id == ShipmentItem.shipment_id)
            .where(
                Shipment.order_id == order_id,
                Shipment.status == ShipmentStatus.SHIPPED.value,
            )
            .group_by(ShipmentItem.order_item_id)
            .subquery()
        )
        requested = (
            select(
                SalesReturnItem.order_item_id.label("order_item_id"),
                func.sum(SalesReturnItem.requested_quantity).label("quantity"),
            )
            .join(SalesReturn, SalesReturn.id == SalesReturnItem.sales_return_id)
            .where(
                SalesReturn.order_id == order_id,
                SalesReturn.status != SalesReturnStatus.CANCELED.value,
            )
            .group_by(SalesReturnItem.order_item_id)
            .subquery()
        )
        stmt = (
            select(
                SalesOrderItem.id,
                SalesOrderItem.product_id,
                func.coalesce(shipped.c.quantity, 0),
                func.coalesce(requested.c.quantity, 0),
            )
            .outerjoin(shipped, shipped.c.order_item_id == SalesOrderItem.id)
            .outerjoin(requested, requested.c.order_item_id == SalesOrderItem.id)
            .where(SalesOrderItem.order_id == order_id)
            .order_by(SalesOrderItem.id)
        )
        return [
            ReturnableOrderItem(
                order_item_id=row[0],
                product_id=row[1],
                shipped_quantity=int(row[2]),
                already_requested_quantity=int(row[3]),
                returnable_quantity=max(int(row[2]) - int(row[3]), 0),
            )
            for row in self.db.execute(stmt)
        ]
