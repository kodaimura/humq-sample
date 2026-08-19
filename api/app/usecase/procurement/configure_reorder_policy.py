from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.error import AppError, ErrorCode
from app.module.business_types import MemberRole, OrganizationKind
from app.module.organization import OrganizationModule
from app.module.product import ProductModule
from app.module.reorder_policy import ReorderPolicy, ReorderPolicyModule
from app.module.warehouse import WarehouseModule
from app.usecase.organizations._operations import RequireOrganizationRoleOperation


@dataclass(frozen=True)
class ConfigureReorderPolicyInput:
    account_id: int
    organization_id: int
    warehouse_id: int
    product_id: int
    preferred_supplier_organization_id: int | None
    reorder_point: int
    target_stock_quantity: int


class ConfigureReorderPolicyUsecase:
    def __init__(self, db: Session):
        self.db = db
        self.require_role = RequireOrganizationRoleOperation(db)
        self.warehouses = WarehouseModule(db)
        self.products = ProductModule(db)
        self.organizations = OrganizationModule(db)
        self.policies = ReorderPolicyModule(db)

    def execute(self, input: ConfigureReorderPolicyInput) -> ReorderPolicy:
        self.require_role.run(
            organization_id=input.organization_id,
            account_id=input.account_id,
            allowed_roles={MemberRole.ADMIN.value, MemberRole.WAREHOUSE.value},
        )
        warehouse = self.warehouses.get_by_id(input.warehouse_id)
        product = self.products.get_by_id(input.product_id)
        if not warehouse or warehouse.organization_id != input.organization_id:
            raise AppError(code=ErrorCode.WAREHOUSE_NOT_FOUND)
        if not product or product.organization_id != input.organization_id:
            raise AppError(code=ErrorCode.PRODUCT_NOT_FOUND)
        if (
            input.reorder_point < 0
            or input.target_stock_quantity <= input.reorder_point
        ):
            raise AppError(code=ErrorCode.INVALID_STATE)
        if input.preferred_supplier_organization_id is not None:
            supplier = self.organizations.get_by_id(
                input.preferred_supplier_organization_id
            )
            if not supplier or supplier.kind != OrganizationKind.SUPPLIER.value:
                raise AppError(code=ErrorCode.ORGANIZATION_NOT_FOUND)
        if self.policies.get(warehouse_id=warehouse.id, product_id=product.id):
            raise AppError(code=ErrorCode.DUPLICATE_CODE)
        policy = self.policies.create(
            warehouse_id=warehouse.id,
            product_id=product.id,
            preferred_supplier_organization_id=input.preferred_supplier_organization_id,
            reorder_point=input.reorder_point,
            target_stock_quantity=input.target_stock_quantity,
        )
        self.db.commit()
        return policy
