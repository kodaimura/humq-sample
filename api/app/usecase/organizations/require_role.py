from sqlalchemy.orm import Session

from app.core.error import AppError, ErrorCode
from app.module.organization import OrganizationModule
from app.module.organization_member import OrganizationMemberModule


class RequireOrganizationRoleUsecase:
    def __init__(self, db: Session):
        self.organizations = OrganizationModule(db)
        self.members = OrganizationMemberModule(db)

    def execute(
        self, *, organization_id: int, account_id: int, allowed_roles: set[str]
    ) -> None:
        if not self.organizations.get_by_id(organization_id):
            raise AppError(code=ErrorCode.ORGANIZATION_NOT_FOUND)
        member = self.members.get(
            organization_id=organization_id, account_id=account_id
        )
        if not member or member.role not in allowed_roles:
            raise AppError(code=ErrorCode.ACCESS_DENIED)
