from sqlalchemy.orm import Session

from .model import AuditLog


class AuditLogModule:
    def __init__(self, db: Session):
        self.db = db

    def record(self, **values) -> AuditLog:
        entity = AuditLog(**values)
        self.db.add(entity)
        self.db.flush()
        self.db.refresh(entity)
        return entity
