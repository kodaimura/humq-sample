from sqlalchemy import select
from sqlalchemy.orm import Session

from .model import InventoryLedger


class InventoryLedgerModule:
    def __init__(self, db: Session):
        self.db = db

    def record(self, **values) -> InventoryLedger:
        entity = InventoryLedger(**values)
        self.db.add(entity)
        self.db.flush()
        self.db.refresh(entity)
        return entity

    def list_by_product(
        self, *, warehouse_id: int, product_id: int, limit: int = 100
    ) -> list[InventoryLedger]:
        stmt = (
            select(InventoryLedger)
            .where(
                InventoryLedger.warehouse_id == warehouse_id,
                InventoryLedger.product_id == product_id,
            )
            .order_by(InventoryLedger.id.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())
