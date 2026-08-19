from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.module.business_types import MemberRole
from app.module.product_category import ProductCategory, ProductCategoryModule
from app.usecase.organizations._operations import RequireOrganizationRoleOperation
from app.usecase._transaction import transactional


@dataclass(frozen=True)
class CreateCategoryInput:
    account_id: int
    organization_id: int
    code: str
    name: str


class CreateCategoryUsecase:
    def __init__(self, db: Session):
        self.db = db
        self.require_role = RequireOrganizationRoleOperation(db)
        self.categories = ProductCategoryModule(db)

    @transactional
    def execute(self, input: CreateCategoryInput) -> ProductCategory:
        self.require_role.run(
            organization_id=input.organization_id,
            account_id=input.account_id,
            allowed_roles={MemberRole.ADMIN.value, MemberRole.SALES.value},
        )
        category = self.categories.create(
            organization_id=input.organization_id, code=input.code, name=input.name
        )
        return category
