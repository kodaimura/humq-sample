from sqlalchemy.orm import Session

from .model import OutboxEvent


class OutboxEventModule:
    def __init__(self, db: Session):
        self.db = db

    def enqueue(self, **values) -> OutboxEvent:
        entity = OutboxEvent(**values)
        self.db.add(entity)
        self.db.flush()
        self.db.refresh(entity)
        return entity
