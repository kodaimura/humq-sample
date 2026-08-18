from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.module.business_types import ShipmentStatus
from app.module.sales_order_item.model import SalesOrderItem
from app.module.shipment.model import Shipment
from app.module.shipment_item.model import ShipmentItem


class OrderFulfillmentQuery:
    def __init__(self, db: Session):
        self.db = db

    def quantities(self, order_id: int) -> tuple[int, int]:
        ordered_stmt = select(
            func.coalesce(func.sum(SalesOrderItem.quantity), 0)
        ).where(SalesOrderItem.order_id == order_id)
        shipped_stmt = (
            select(func.coalesce(func.sum(ShipmentItem.quantity), 0))
            .join(Shipment, Shipment.id == ShipmentItem.shipment_id)
            .where(
                Shipment.order_id == order_id,
                Shipment.status == ShipmentStatus.SHIPPED.value,
            )
        )
        return int(self.db.scalar(ordered_stmt) or 0), int(
            self.db.scalar(shipped_stmt) or 0
        )
