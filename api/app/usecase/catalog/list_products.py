from sqlalchemy.orm import Session

from app.module.business_types import MemberRole
from app.module.product import Product, ProductModule
from app.usecase.organizations._operations import RequireOrganizationRoleOperation


class ListProductsUsecase:
    def __init__(self, db: Session):
        self.require_role = RequireOrganizationRoleOperation(db)
        self.products = ProductModule(db)

    def execute(self, *, account_id: int, organization_id: int) -> list[Product]:
        self.require_role.run(
            organization_id=organization_id,
            account_id=account_id,
            allowed_roles={role.value for role in MemberRole},
        )
        return self.products.list_by_organization(organization_id)
