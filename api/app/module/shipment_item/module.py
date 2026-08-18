from sqlalchemy import select
from sqlalchemy.orm import Session

from .model import ShipmentItem


class ShipmentItemModule:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **values) -> ShipmentItem:
        entity = ShipmentItem(**values)
        self.db.add(entity)
        self.db.flush()
        self.db.refresh(entity)
        return entity

    def list_by_shipment(self, shipment_id: int) -> list[ShipmentItem]:
        stmt = select(ShipmentItem).where(
            ShipmentItem.shipment_id == shipment_id
        ).order_by(ShipmentItem.id)
        return list(self.db.scalars(stmt).all())
