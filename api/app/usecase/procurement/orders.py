from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
import secrets

from sqlalchemy.orm import Session

from app.core.error import AppError, ErrorCode
from app.module.audit_log import AuditLogModule
from app.module.business_types import MemberRole, OrganizationKind, PurchaseOrderStatus
from app.module.organization import OrganizationModule
from app.module.outbox_event import OutboxEventModule
from app.module.product import ProductModule
from app.module.purchase_order import PurchaseOrder, PurchaseOrderModule
from app.module.purchase_order_item import PurchaseOrderItemModule
from app.module.purchase_order_status_history import PurchaseOrderStatusHistoryModule
from app.module.supplier_product import SupplierProductModule
from app.module.warehouse import WarehouseModule
from app.usecase.organizations.require_role import RequireOrganizationRoleUsecase


@dataclass(frozen=True)
class PurchaseOrderLineInput:
    product_id: int
    quantity: int
    unit_cost: Decimal | None = None


@dataclass(frozen=True)
class CreatePurchaseOrderInput:
    account_id: int
    buyer_organization_id: int
    supplier_organization_id: int
    warehouse_id: int
    expected_date: date | None
    note: str | None
    items: list[PurchaseOrderLineInput]


class CreatePurchaseOrderUsecase:
    def __init__(self, db: Session):
        self.db = db
        self.require_role = RequireOrganizationRoleUsecase(db)
        self.organizations = OrganizationModule(db)
        self.warehouses = WarehouseModule(db)
        self.products = ProductModule(db)
        self.supplier_products = SupplierProductModule(db)
        self.orders = PurchaseOrderModule(db)
        self.items = PurchaseOrderItemModule(db)
        self.history = PurchaseOrderStatusHistoryModule(db)
        self.audit_logs = AuditLogModule(db)

    def execute(self, input: CreatePurchaseOrderInput) -> PurchaseOrder:
        self.require_role.execute(
            organization_id=input.buyer_organization_id,
            account_id=input.account_id,
            allowed_roles={MemberRole.ADMIN.value, MemberRole.WAREHOUSE.value},
        )
        supplier = self.organizations.get_by_id(input.supplier_organization_id)
        warehouse = self.warehouses.get_by_id(input.warehouse_id)
        if not supplier or supplier.kind != OrganizationKind.SUPPLIER.value:
            raise AppError(code=ErrorCode.ORGANIZATION_NOT_FOUND)
        if not warehouse or warehouse.organization_id != input.buyer_organization_id:
            raise AppError(code=ErrorCode.WAREHOUSE_NOT_FOUND)
        if not input.items or len({item.product_id for item in input.items}) != len(input.items):
            raise AppError(code=ErrorCode.INVALID_STATE)
        order = self.orders.create(
            purchase_order_number=_new_number("PO"),
            buyer_organization_id=input.buyer_organization_id,
            supplier_organization_id=input.supplier_organization_id,
            warehouse_id=input.warehouse_id,
            order_date=date.today(),
            expected_date=input.expected_date,
            note=input.note,
            created_by_account_id=input.account_id,
        )
        subtotal = Decimal("0.00")
        for line in input.items:
            product = self.products.get_by_id(line.product_id)
            supplier_product = self.supplier_products.get(
                supplier_organization_id=supplier.id, product_id=line.product_id
            )
            if not product or product.organization_id != input.buyer_organization_id:
                raise AppError(code=ErrorCode.PRODUCT_NOT_FOUND)
            if line.quantity <= 0 or (supplier_product and line.quantity < supplier_product.minimum_order_quantity):
                raise AppError(code=ErrorCode.INVALID_STATE)
            unit_cost = line.unit_cost or (supplier_product.unit_cost if supplier_product else None)
            if unit_cost is None or unit_cost <= 0:
                raise AppError(code=ErrorCode.SUPPLIER_PRODUCT_NOT_FOUND)
            line_subtotal = (unit_cost * line.quantity).quantize(Decimal("0.01"))
            self.items.create(
                purchase_order_id=order.id,
                product_id=product.id,
                supplier_product_id=supplier_product.id if supplier_product else None,
                quantity=line.quantity,
                unit_cost=unit_cost,
                subtotal=line_subtotal,
            )
            subtotal += line_subtotal
        tax = (subtotal * Decimal("0.10")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        self.orders.set_totals(order, subtotal=subtotal, tax_amount=tax, total_amount=subtotal + tax)
        self.history.create(purchase_order_id=order.id, from_status=None, to_status=PurchaseOrderStatus.DRAFT.value, reason=None, changed_by_account_id=input.account_id)
        self.audit_logs.record(actor_account_id=input.account_id, action="purchase_order.created", resource_type="purchase_order", resource_id=order.id, details={"line_count": len(input.items)})
        self.db.commit()
        return order


class ChangePurchaseOrderStatusUsecase:
    def __init__(self, db: Session):
        self.db = db; self.require_role = RequireOrganizationRoleUsecase(db); self.orders = PurchaseOrderModule(db); self.history = PurchaseOrderStatusHistoryModule(db); self.outbox = OutboxEventModule(db); self.audit = AuditLogModule(db)

    def execute(self, *, account_id: int, purchase_order_id: int, action: str, reason: str | None = None) -> PurchaseOrder:
        order = self.orders.get_for_update(purchase_order_id)
        if not order: raise AppError(code=ErrorCode.PURCHASE_ORDER_NOT_FOUND)
        self.require_role.execute(organization_id=order.buyer_organization_id, account_id=account_id, allowed_roles={MemberRole.ADMIN.value, MemberRole.WAREHOUSE.value})
        transitions = {"approve": ({PurchaseOrderStatus.DRAFT.value}, PurchaseOrderStatus.APPROVED.value), "cancel": ({PurchaseOrderStatus.DRAFT.value, PurchaseOrderStatus.APPROVED.value}, PurchaseOrderStatus.CANCELED.value)}
        allowed, target = transitions.get(action, (set(), ""))
        if order.status not in allowed: raise AppError(code=ErrorCode.INVALID_PURCHASE_ORDER_STATE)
        previous = self.orders.change_status(order, target)
        self.history.create(purchase_order_id=order.id, from_status=previous, to_status=target, reason=reason, changed_by_account_id=account_id)
        self.outbox.enqueue(event_type=f"purchase_order.{target.lower()}", aggregate_type="purchase_order", aggregate_id=order.id, payload={"purchase_order_id": order.id, "status": target})
        self.audit.record(actor_account_id=account_id, action=f"purchase_order.{target.lower()}", resource_type="purchase_order", resource_id=order.id, details={"reason": reason})
        self.db.commit(); return order


def _new_number(prefix: str) -> str:
    return f"{prefix}-{date.today():%Y%m%d}-{secrets.token_hex(3).upper()}"
