from sqlalchemy import select
from sqlalchemy.orm import Session

from .model import Organization


class OrganizationModule:
    def __init__(self, db: Session):
        self.db = db

    def create(self, *, code: str, name: str, kind: str, note: str | None = None) -> Organization:
        entity = Organization(code=code, name=name, kind=kind, note=note)
        self.db.add(entity)
        self.db.flush()
        self.db.refresh(entity)
        return entity

    def get_by_id(self, organization_id: int) -> Organization | None:
        stmt = select(Organization).where(
            Organization.id == organization_id, Organization.deleted_at.is_(None)
        )
        return self.db.scalars(stmt).first()

    def get_by_code(self, code: str) -> Organization | None:
        stmt = select(Organization).where(
            Organization.code == code, Organization.deleted_at.is_(None)
        )
        return self.db.scalars(stmt).first()

    def list_all(self) -> list[Organization]:
        stmt = select(Organization).where(Organization.deleted_at.is_(None)).order_by(Organization.name)
        return list(self.db.scalars(stmt).all())
