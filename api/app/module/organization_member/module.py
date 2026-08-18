from sqlalchemy import select
from sqlalchemy.orm import Session

from .model import OrganizationMember


class OrganizationMemberModule:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self, *, organization_id: int, account_id: int, role: str
    ) -> OrganizationMember:
        entity = OrganizationMember(
            organization_id=organization_id, account_id=account_id, role=role
        )
        self.db.add(entity)
        self.db.flush()
        self.db.refresh(entity)
        return entity

    def get(
        self, *, organization_id: int, account_id: int
    ) -> OrganizationMember | None:
        stmt = select(OrganizationMember).where(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.account_id == account_id,
        )
        return self.db.scalars(stmt).first()

    def list_by_account(self, account_id: int) -> list[OrganizationMember]:
        stmt = (
            select(OrganizationMember)
            .where(OrganizationMember.account_id == account_id)
            .order_by(OrganizationMember.organization_id)
        )
        return list(self.db.scalars(stmt).all())
