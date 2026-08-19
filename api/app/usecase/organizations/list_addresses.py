from sqlalchemy.orm import Session

from app.module.business_types import MemberRole
from app.module.organization_address import (
    OrganizationAddress,
    OrganizationAddressModule,
)

from ._operations import RequireOrganizationRoleOperation


class ListOrganizationAddressesUsecase:
    def __init__(self, db: Session):
        self.require_role = RequireOrganizationRoleOperation(db)
        self.addresses = OrganizationAddressModule(db)

    def execute(
        self, *, account_id: int, organization_id: int
    ) -> list[OrganizationAddress]:
        self.require_role.run(
            organization_id=organization_id,
            account_id=account_id,
            allowed_roles={role.value for role in MemberRole},
        )
        return self.addresses.list_by_organization(organization_id)
