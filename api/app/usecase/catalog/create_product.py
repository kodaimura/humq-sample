from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.error import AppError, ErrorCode
from app.module.business_types import MemberRole
from app.module.product import Product, ProductModule
from app.module.product_category import ProductCategoryModule
from app.usecase.organizations._operations import RequireOrganizationRoleOperation
from app.usecase._transaction import transactional


@dataclass(frozen=True)
class CreateProductInput:
    account_id: int
    organization_id: int
    category_id: int | None
    sku: str
    name: str
    description: str | None
    unit_price: Decimal


class CreateProductUsecase:
    def __init__(self, db: Session):
        self.db = db
        self.require_role = RequireOrganizationRoleOperation(db)
        self.categories = ProductCategoryModule(db)
        self.products = ProductModule(db)

    @transactional
    def execute(self, input: CreateProductInput) -> Product:
        self.require_role.run(
            organization_id=input.organization_id,
            account_id=input.account_id,
            allowed_roles={MemberRole.ADMIN.value, MemberRole.SALES.value},
        )
        if input.category_id is not None:
            category = self.categories.get_by_id(input.category_id)
            if not category or category.organization_id != input.organization_id:
                raise AppError(code=ErrorCode.CATEGORY_NOT_FOUND)
        if self.products.get_by_sku(
            organization_id=input.organization_id, sku=input.sku
        ):
            raise AppError(code=ErrorCode.DUPLICATE_CODE)
        product = self.products.create(
            organization_id=input.organization_id,
            category_id=input.category_id,
            sku=input.sku,
            name=input.name,
            description=input.description,
            unit_price=input.unit_price,
        )
        return product
