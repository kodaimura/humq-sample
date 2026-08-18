from sqlalchemy import select
from sqlalchemy.orm import Session

from .model import SalesOrderStatusHistory


class SalesOrderStatusHistoryModule:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **values) -> SalesOrderStatusHistory:
        entity = SalesOrderStatusHistory(**values)
        self.db.add(entity)
        self.db.flush()
        self.db.refresh(entity)
        return entity

    def list_by_order(self, order_id: int) -> list[SalesOrderStatusHistory]:
        stmt = (
            select(SalesOrderStatusHistory)
            .where(SalesOrderStatusHistory.order_id == order_id)
            .order_by(SalesOrderStatusHistory.id)
        )
        return list(self.db.scalars(stmt).all())
