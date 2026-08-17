from sqlalchemy import select
from sqlalchemy.orm import Session

from .model import StockReservation


class StockReservationModule:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **values) -> StockReservation:
        entity = StockReservation(**values)
        self.db.add(entity)
        self.db.flush()
        self.db.refresh(entity)
        return entity

    def list_by_order_item(self, order_item_id: int) -> list[StockReservation]:
        stmt = select(StockReservation).where(
            StockReservation.order_item_id == order_item_id
        ).order_by(StockReservation.id)
        return list(self.db.scalars(stmt).all())

    def list_by_order_items(
        self, order_item_ids: list[int], status: str | None = None
    ) -> list[StockReservation]:
        if not order_item_ids:
            return []
        stmt = select(StockReservation).where(
            StockReservation.order_item_id.in_(order_item_ids)
        )
        if status is not None:
            stmt = stmt.where(StockReservation.status == status)
        return list(self.db.scalars(stmt.order_by(StockReservation.id)).all())

    def set_status(self, entity: StockReservation, status: str) -> None:
        entity.status = status
        self.db.flush()
