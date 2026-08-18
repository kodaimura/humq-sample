from sqlalchemy import select
from sqlalchemy.orm import Session
from .model import SalesReturnStatusHistory


class SalesReturnStatusHistoryModule:
    def __init__(self, db: Session): self.db = db
    def create(self, **values) -> SalesReturnStatusHistory:
        entity = SalesReturnStatusHistory(**values); self.db.add(entity); self.db.flush(); self.db.refresh(entity); return entity
    def list_by_return(self, sales_return_id: int) -> list[SalesReturnStatusHistory]:
        return list(self.db.scalars(select(SalesReturnStatusHistory).where(SalesReturnStatusHistory.sales_return_id == sales_return_id).order_by(SalesReturnStatusHistory.id)).all())
