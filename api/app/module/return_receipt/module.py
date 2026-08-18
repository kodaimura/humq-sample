from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.module.business_types import ReturnReceiptStatus
from .model import ReturnReceipt


class ReturnReceiptModule:
    def __init__(self, db: Session): self.db = db
    def create(self, **values) -> ReturnReceipt:
        entity = ReturnReceipt(**values); self.db.add(entity); self.db.flush(); self.db.refresh(entity); return entity
    def get_by_id(self, entity_id: int) -> ReturnReceipt | None: return self.db.get(ReturnReceipt, entity_id)
    def get_for_update(self, entity_id: int) -> ReturnReceipt | None:
        return self.db.scalars(select(ReturnReceipt).where(ReturnReceipt.id == entity_id).with_for_update()).first()
    def list_by_return(self, sales_return_id: int) -> list[ReturnReceipt]:
        return list(self.db.scalars(select(ReturnReceipt).where(ReturnReceipt.sales_return_id == sales_return_id).order_by(ReturnReceipt.id.desc())).all())
    def post(self, entity: ReturnReceipt) -> None:
        entity.status = ReturnReceiptStatus.POSTED.value; entity.posted_at = datetime.now(timezone.utc); self.db.flush()
