from sqlalchemy import select
from sqlalchemy.orm import Session
from .model import PurchaseOrderStatusHistory


class PurchaseOrderStatusHistoryModule:
    def __init__(self, db: Session): self.db = db
    def create(self, **values) -> PurchaseOrderStatusHistory:
        entity = PurchaseOrderStatusHistory(**values); self.db.add(entity); self.db.flush(); self.db.refresh(entity); return entity
    def list_by_order(self, purchase_order_id: int) -> list[PurchaseOrderStatusHistory]:
        return list(self.db.scalars(select(PurchaseOrderStatusHistory).where(PurchaseOrderStatusHistory.purchase_order_id == purchase_order_id).order_by(PurchaseOrderStatusHistory.id)).all())
