from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.module.business_types import GoodsReceiptStatus
from .model import GoodsReceipt


class GoodsReceiptModule:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **values) -> GoodsReceipt:
        entity = GoodsReceipt(**values)
        self.db.add(entity)
        self.db.flush()
        self.db.refresh(entity)
        return entity

    def get_by_id(self, entity_id: int) -> GoodsReceipt | None:
        return self.db.get(GoodsReceipt, entity_id)

    def get_for_update(self, entity_id: int) -> GoodsReceipt | None:
        return self.db.scalars(
            select(GoodsReceipt).where(GoodsReceipt.id == entity_id).with_for_update()
        ).first()

    def list_by_order(self, purchase_order_id: int) -> list[GoodsReceipt]:
        return list(
            self.db.scalars(
                select(GoodsReceipt)
                .where(GoodsReceipt.purchase_order_id == purchase_order_id)
                .order_by(GoodsReceipt.id.desc())
            ).all()
        )

    def post(self, entity: GoodsReceipt) -> str:
        previous = entity.status
        entity.status = GoodsReceiptStatus.POSTED.value
        entity.posted_at = datetime.now(timezone.utc)
        self.db.flush()
        return previous
