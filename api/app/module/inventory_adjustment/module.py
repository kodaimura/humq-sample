from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.module.business_types import AdjustmentStatus
from .model import InventoryAdjustment


class InventoryAdjustmentModule:
    def __init__(self, db: Session):
        self.db = db

    def create(self, *, warehouse_id: int, reason: str, created_by_account_id: int) -> InventoryAdjustment:
        entity = InventoryAdjustment(
            warehouse_id=warehouse_id,
            reason=reason,
            created_by_account_id=created_by_account_id,
        )
        self.db.add(entity)
        self.db.flush()
        self.db.refresh(entity)
        return entity

    def get_for_update(self, adjustment_id: int) -> InventoryAdjustment | None:
        stmt = select(InventoryAdjustment).where(
            InventoryAdjustment.id == adjustment_id
        ).with_for_update()
        return self.db.scalars(stmt).first()

    def mark_applied(self, entity: InventoryAdjustment) -> None:
        entity.status = AdjustmentStatus.APPLIED.value
        entity.applied_at = datetime.now(timezone.utc)
        self.db.flush()
