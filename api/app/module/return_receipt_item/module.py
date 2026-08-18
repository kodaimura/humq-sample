from sqlalchemy import select
from sqlalchemy.orm import Session
from .model import ReturnReceiptItem


class ReturnReceiptItemModule:
    def __init__(self, db: Session): self.db = db
    def create(self, **values) -> ReturnReceiptItem:
        entity = ReturnReceiptItem(**values); self.db.add(entity); self.db.flush(); self.db.refresh(entity); return entity
    def list_by_receipt(self, return_receipt_id: int) -> list[ReturnReceiptItem]:
        return list(self.db.scalars(select(ReturnReceiptItem).where(ReturnReceiptItem.return_receipt_id == return_receipt_id).order_by(ReturnReceiptItem.id)).all())
