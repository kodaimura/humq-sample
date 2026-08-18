from sqlalchemy import select
from sqlalchemy.orm import Session

from .model import PurchaseOrderItem


class PurchaseOrderItemModule:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **values) -> PurchaseOrderItem:
        entity = PurchaseOrderItem(**values)
        self.db.add(entity)
        self.db.flush()
        self.db.refresh(entity)
        return entity

    def get_by_id(self, entity_id: int) -> PurchaseOrderItem | None:
        return self.db.get(PurchaseOrderItem, entity_id)

    def get_for_update(self, entity_id: int) -> PurchaseOrderItem | None:
        return self.db.scalars(
            select(PurchaseOrderItem)
            .where(PurchaseOrderItem.id == entity_id)
            .with_for_update()
        ).first()

    def list_by_order(self, purchase_order_id: int) -> list[PurchaseOrderItem]:
        return list(
            self.db.scalars(
                select(PurchaseOrderItem)
                .where(PurchaseOrderItem.purchase_order_id == purchase_order_id)
                .order_by(PurchaseOrderItem.id)
            ).all()
        )

    def receive(self, entity: PurchaseOrderItem, quantity: int) -> bool:
        if quantity <= 0 or entity.received_quantity + quantity > entity.quantity:
            return False
        entity.received_quantity += quantity
        self.db.flush()
        return True
