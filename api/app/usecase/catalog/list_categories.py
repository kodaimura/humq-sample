from sqlalchemy.orm import Session

from app.module.business_types import MemberRole
from app.module.product_category import ProductCategory, ProductCategoryModule
from app.usecase.organizations._operations import RequireOrganizationRoleOperation


class ListCategoriesUsecase:
    def __init__(self, db: Session):
        self.require_role = RequireOrganizationRoleOperation(db)
        self.categories = ProductCategoryModule(db)

    def execute(
        self, *, account_id: int, organization_id: int
    ) -> list[ProductCategory]:
        self.require_role.run(
            organization_id=organization_id,
            account_id=account_id,
            allowed_roles={role.value for role in MemberRole},
        )
        return self.categories.list_by_organization(organization_id)
