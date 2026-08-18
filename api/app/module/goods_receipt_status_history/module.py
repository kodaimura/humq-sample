from sqlalchemy import select
from sqlalchemy.orm import Session
from .model import GoodsReceiptStatusHistory


class GoodsReceiptStatusHistoryModule:
    def __init__(self, db: Session): self.db = db
    def create(self, **values) -> GoodsReceiptStatusHistory:
        entity = GoodsReceiptStatusHistory(**values); self.db.add(entity); self.db.flush(); self.db.refresh(entity); return entity
    def list_by_receipt(self, goods_receipt_id: int) -> list[GoodsReceiptStatusHistory]:
        return list(self.db.scalars(select(GoodsReceiptStatusHistory).where(GoodsReceiptStatusHistory.goods_receipt_id == goods_receipt_id).order_by(GoodsReceiptStatusHistory.id)).all())
