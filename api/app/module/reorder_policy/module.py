from sqlalchemy import select
from sqlalchemy.orm import Session

from .model import ReorderPolicy


class ReorderPolicyModule:
    def __init__(self, db: Session): self.db = db
    def create(self, **values) -> ReorderPolicy:
        entity = ReorderPolicy(**values); self.db.add(entity); self.db.flush(); self.db.refresh(entity); return entity
    def get_by_id(self, entity_id: int) -> ReorderPolicy | None: return self.db.get(ReorderPolicy, entity_id)
    def get(self, *, warehouse_id: int, product_id: int) -> ReorderPolicy | None:
        return self.db.scalars(select(ReorderPolicy).where(ReorderPolicy.warehouse_id == warehouse_id, ReorderPolicy.product_id == product_id)).first()
    def list_by_warehouse(self, warehouse_id: int) -> list[ReorderPolicy]:
        return list(self.db.scalars(select(ReorderPolicy).where(ReorderPolicy.warehouse_id == warehouse_id).order_by(ReorderPolicy.product_id)).all())
