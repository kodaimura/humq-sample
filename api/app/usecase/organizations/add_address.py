from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.module.business_types import MemberRole
from app.module.organization_address import OrganizationAddress, OrganizationAddressModule
from ._operations import RequireOrganizationRoleOperation


@dataclass(frozen=True)
class AddOrganizationAddressInput:
    account_id: int
    organization_id: int
    kind: str
    name: str
    postal_code: str
    prefecture: str
    city: str
    address_line1: str
    address_line2: str | None
    recipient_name: str
    phone: str | None
    is_default: bool


class AddOrganizationAddressUsecase:
    def __init__(self, db: Session):
        self.db = db
        self.require_role = RequireOrganizationRoleOperation(db)
        self.addresses = OrganizationAddressModule(db)

    def execute(self, input: AddOrganizationAddressInput) -> OrganizationAddress:
        self.require_role.run(
            organization_id=input.organization_id,
            account_id=input.account_id,
            allowed_roles={MemberRole.ADMIN.value, MemberRole.SALES.value},
        )
        address = self.addresses.create(
            **{key: value for key, value in input.__dict__.items() if key != "account_id"}
        )
        self.db.commit()
        return address


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
