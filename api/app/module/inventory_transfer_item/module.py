from sqlalchemy import select
from sqlalchemy.orm import Session

from .model import InventoryTransferItem


class InventoryTransferItemModule:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self, *, transfer_id: int, product_id: int, quantity: int
    ) -> InventoryTransferItem:
        entity = InventoryTransferItem(
            transfer_id=transfer_id, product_id=product_id, quantity=quantity
        )
        self.db.add(entity)
        self.db.flush()
        self.db.refresh(entity)
        return entity

    def list_by_transfer(self, transfer_id: int) -> list[InventoryTransferItem]:
        stmt = (
            select(InventoryTransferItem)
            .where(InventoryTransferItem.transfer_id == transfer_id)
            .order_by(InventoryTransferItem.id)
        )
        return list(self.db.scalars(stmt).all())
