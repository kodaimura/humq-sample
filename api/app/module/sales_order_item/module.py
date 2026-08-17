from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from .model import SalesOrderItem


class SalesOrderItemModule:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        *,
        order_id: int,
        product_id: int,
        quantity: int,
        unit_price: Decimal,
    ) -> SalesOrderItem:
        entity = SalesOrderItem(
            order_id=order_id,
            product_id=product_id,
            quantity=quantity,
            unit_price=unit_price,
            subtotal=unit_price * quantity,
        )
        self.db.add(entity)
        self.db.flush()
        self.db.refresh(entity)
        return entity

    def list_by_order(self, order_id: int) -> list[SalesOrderItem]:
        stmt = select(SalesOrderItem).where(
            SalesOrderItem.order_id == order_id
        ).order_by(SalesOrderItem.id)
        return list(self.db.scalars(stmt).all())

    def get_by_id(self, order_item_id: int) -> SalesOrderItem | None:
        return self.db.get(SalesOrderItem, order_item_id)
