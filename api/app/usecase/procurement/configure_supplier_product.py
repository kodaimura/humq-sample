from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.error import AppError, ErrorCode
from app.module.audit_log import AuditLogModule
from app.module.business_types import MemberRole, OrganizationKind
from app.module.organization import OrganizationModule
from app.module.product import ProductModule
from app.module.supplier_product import SupplierProduct, SupplierProductModule
from app.usecase.organizations._operations import RequireOrganizationRoleOperation


@dataclass(frozen=True)
class ConfigureSupplierProductInput:
    account_id: int
    buyer_organization_id: int
    supplier_organization_id: int
    product_id: int
    supplier_sku: str
    unit_cost: Decimal
    lead_time_days: int
    minimum_order_quantity: int


class ConfigureSupplierProductUsecase:
    def __init__(self, db: Session):
        self.db = db
        self.require_role = RequireOrganizationRoleOperation(db)
        self.organizations = OrganizationModule(db)
        self.products = ProductModule(db)
        self.supplier_products = SupplierProductModule(db)
        self.audit_logs = AuditLogModule(db)

    def execute(self, input: ConfigureSupplierProductInput) -> SupplierProduct:
        self.require_role.run(
            organization_id=input.buyer_organization_id,
            account_id=input.account_id,
            allowed_roles={MemberRole.ADMIN.value, MemberRole.WAREHOUSE.value},
        )
        supplier = self.organizations.get_by_id(input.supplier_organization_id)
        product = self.products.get_by_id(input.product_id)
        if not supplier or supplier.kind != OrganizationKind.SUPPLIER.value:
            raise AppError(code=ErrorCode.ORGANIZATION_NOT_FOUND)
        if not product or product.organization_id != input.buyer_organization_id:
            raise AppError(code=ErrorCode.PRODUCT_NOT_FOUND)
        if (
            input.unit_cost <= 0
            or input.lead_time_days < 0
            or input.minimum_order_quantity <= 0
        ):
            raise AppError(code=ErrorCode.INVALID_STATE)
        if self.supplier_products.get(
            supplier_organization_id=supplier.id, product_id=product.id
        ):
            raise AppError(code=ErrorCode.DUPLICATE_CODE)
        entity = self.supplier_products.create(
            supplier_organization_id=supplier.id,
            product_id=product.id,
            supplier_sku=input.supplier_sku,
            unit_cost=input.unit_cost,
            lead_time_days=input.lead_time_days,
            minimum_order_quantity=input.minimum_order_quantity,
        )
        self.audit_logs.record(
            actor_account_id=input.account_id,
            action="supplier_product.configured",
            resource_type="supplier_product",
            resource_id=entity.id,
            details={"supplier_id": supplier.id, "product_id": product.id},
        )
        self.db.commit()
        return entity
