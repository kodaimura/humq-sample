from sqlalchemy.orm import Session

from .model import ShipmentStatusHistory


class ShipmentStatusHistoryModule:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **values) -> ShipmentStatusHistory:
        entity = ShipmentStatusHistory(**values)
        self.db.add(entity)
        self.db.flush()
        self.db.refresh(entity)
        return entity
