from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.error import AppError, ErrorCode
from app.module.audit_log import AuditLogModule
from app.module.business_types import MemberRole
from app.module.organization import Organization, OrganizationModule
from app.module.organization_member import OrganizationMemberModule


@dataclass(frozen=True)
class CreateOrganizationInput:
    account_id: int
    code: str
    name: str
    kind: str
    note: str | None


class CreateOrganizationUsecase:
    def __init__(self, db: Session):
        self.db = db
        self.organizations = OrganizationModule(db)
        self.members = OrganizationMemberModule(db)
        self.audit_logs = AuditLogModule(db)

    def execute(self, input: CreateOrganizationInput) -> Organization:
        if self.organizations.get_by_code(input.code):
            raise AppError(code=ErrorCode.DUPLICATE_CODE)
        try:
            organization = self.organizations.create(
                code=input.code, name=input.name, kind=input.kind, note=input.note
            )
            self.members.create(
                organization_id=organization.id,
                account_id=input.account_id,
                role=MemberRole.ADMIN.value,
            )
            self.audit_logs.record(
                actor_account_id=input.account_id,
                action="organization.created",
                resource_type="organization",
                resource_id=organization.id,
                details={"code": input.code, "kind": input.kind},
            )
            self.db.commit()
            return organization
        except IntegrityError as exc:
            self.db.rollback()
            raise AppError(code=ErrorCode.DUPLICATE_CODE) from exc
