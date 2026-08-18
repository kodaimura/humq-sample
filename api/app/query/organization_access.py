from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.module.organization.model import Organization
from app.module.organization_member.model import OrganizationMember


@dataclass(frozen=True)
class OrganizationAccessView:
    organization_id: int
    code: str
    name: str
    kind: str
    status: str
    role: str


class OrganizationAccessQuery:
    def __init__(self, db: Session):
        self.db = db

    def list_for_account(self, account_id: int) -> list[OrganizationAccessView]:
        stmt = (
            select(
                Organization.id.label("organization_id"),
                Organization.code,
                Organization.name,
                Organization.kind,
                Organization.status,
                OrganizationMember.role,
            )
            .join(
                OrganizationMember,
                OrganizationMember.organization_id == Organization.id,
            )
            .where(
                OrganizationMember.account_id == account_id,
                Organization.deleted_at.is_(None),
            )
            .order_by(Organization.name)
        )
        return [OrganizationAccessView(**row._mapping) for row in self.db.execute(stmt)]
