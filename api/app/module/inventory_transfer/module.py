from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.module.business_types import TransferStatus
from .model import InventoryTransfer


class InventoryTransferModule:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **values) -> InventoryTransfer:
        entity = InventoryTransfer(**values)
        self.db.add(entity)
        self.db.flush()
        self.db.refresh(entity)
        return entity

    def get_for_update(self, transfer_id: int) -> InventoryTransfer | None:
        stmt = (
            select(InventoryTransfer)
            .where(InventoryTransfer.id == transfer_id)
            .with_for_update()
        )
        return self.db.scalars(stmt).first()

    def mark_in_transit(self, entity: InventoryTransfer) -> None:
        entity.status = TransferStatus.IN_TRANSIT.value
        entity.shipped_at = datetime.now(timezone.utc)
        self.db.flush()

    def mark_received(self, entity: InventoryTransfer) -> None:
        entity.status = TransferStatus.RECEIVED.value
        entity.received_at = datetime.now(timezone.utc)
        self.db.flush()
