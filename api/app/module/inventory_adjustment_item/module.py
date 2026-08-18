from sqlalchemy import select
from sqlalchemy.orm import Session

from .model import InventoryAdjustmentItem


class InventoryAdjustmentItemModule:
    def __init__(self, db: Session):
        self.db = db

    def create(self, *, adjustment_id: int, product_id: int, quantity_delta: int, note: str | None) -> InventoryAdjustmentItem:
        entity = InventoryAdjustmentItem(
            adjustment_id=adjustment_id,
            product_id=product_id,
            quantity_delta=quantity_delta,
            note=note,
        )
        self.db.add(entity)
        self.db.flush()
        self.db.refresh(entity)
        return entity

    def list_by_adjustment(self, adjustment_id: int) -> list[InventoryAdjustmentItem]:
        stmt = select(InventoryAdjustmentItem).where(
            InventoryAdjustmentItem.adjustment_id == adjustment_id
        ).order_by(InventoryAdjustmentItem.id)
        return list(self.db.scalars(stmt).all())
