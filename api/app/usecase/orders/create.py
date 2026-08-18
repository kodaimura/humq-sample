from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
import secrets

from sqlalchemy.orm import Session

from app.core.error import AppError, ErrorCode
from app.module.audit_log import AuditLogModule
from app.module.business_types import MemberRole, OrderStatus, OrganizationStatus
from app.module.customer_product_price import CustomerProductPriceModule
from app.module.organization import OrganizationModule
from app.module.organization_address import OrganizationAddressModule
from app.module.product import ProductModule
from app.module.sales_order import SalesOrder, SalesOrderModule
from app.module.sales_order_item import SalesOrderItemModule
from app.module.sales_order_status_history import SalesOrderStatusHistoryModule
from app.usecase.organizations._operations import RequireOrganizationRoleOperation


@dataclass(frozen=True)
class CreateOrderLineInput:
    product_id: int
    quantity: int


@dataclass(frozen=True)
class CreateOrderInput:
    account_id: int
    seller_organization_id: int
    customer_organization_id: int
    shipping_address_id: int | None
    requested_ship_date: date | None
    note: str | None
    items: list[CreateOrderLineInput]


class CreateOrderUsecase:
    def __init__(self, db: Session):
        self.db = db
        self.require_role = RequireOrganizationRoleOperation(db)
        self.organizations = OrganizationModule(db)
        self.addresses = OrganizationAddressModule(db)
        self.products = ProductModule(db)
        self.prices = CustomerProductPriceModule(db)
        self.orders = SalesOrderModule(db)
        self.order_items = SalesOrderItemModule(db)
        self.history = SalesOrderStatusHistoryModule(db)
        self.audit_logs = AuditLogModule(db)

    def execute(self, input: CreateOrderInput) -> SalesOrder:
        self.require_role.run(
            organization_id=input.seller_organization_id,
            account_id=input.account_id,
            allowed_roles={MemberRole.ADMIN.value, MemberRole.SALES.value},
        )
        customer = self.organizations.get_by_id(input.customer_organization_id)
        if not customer or customer.status != OrganizationStatus.ACTIVE.value:
            raise AppError(code=ErrorCode.ORGANIZATION_NOT_FOUND)
        if input.shipping_address_id is not None:
            address = self.addresses.get_by_id(input.shipping_address_id)
            if not address or address.organization_id != customer.id:
                raise AppError(code=ErrorCode.ADDRESS_NOT_FOUND)
        if not input.items or len({item.product_id for item in input.items}) != len(
            input.items
        ):
            raise AppError(code=ErrorCode.INVALID_STATE)

        order = self.orders.create(
            order_number=_new_order_number(),
            seller_organization_id=input.seller_organization_id,
            customer_organization_id=input.customer_organization_id,
            shipping_address_id=input.shipping_address_id,
            requested_ship_date=input.requested_ship_date,
            note=input.note,
            ordered_by_account_id=input.account_id,
        )
        subtotal = Decimal("0.00")
        today = date.today()
        for line in input.items:
            if line.quantity <= 0:
                raise AppError(code=ErrorCode.INVALID_STATE)
            product = self.products.get_by_id(line.product_id)
            if (
                not product
                or product.organization_id != input.seller_organization_id
                or not product.active
            ):
                raise AppError(code=ErrorCode.PRODUCT_NOT_FOUND)
            customer_price = self.prices.find_effective(
                customer_organization_id=input.customer_organization_id,
                product_id=product.id,
                on_date=today,
            )
            unit_price = (
                customer_price.unit_price if customer_price else product.unit_price
            )
            item = self.order_items.create(
                order_id=order.id,
                product_id=product.id,
                quantity=line.quantity,
                unit_price=unit_price,
            )
            subtotal += item.subtotal

        tax_amount = (subtotal * Decimal("0.10")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        self.orders.set_totals(
            order,
            subtotal=subtotal,
            tax_amount=tax_amount,
            total_amount=subtotal + tax_amount,
        )
        self.history.create(
            order_id=order.id,
            from_status=None,
            to_status=OrderStatus.DRAFT.value,
            changed_by_account_id=input.account_id,
        )
        self.audit_logs.record(
            actor_account_id=input.account_id,
            action="order.created",
            resource_type="sales_order",
            resource_id=order.id,
            details={
                "order_number": order.order_number,
                "line_count": len(input.items),
            },
        )
        self.db.commit()
        return order


def _new_order_number() -> str:
    return f"SO-{date.today():%Y%m%d}-{secrets.token_hex(3).upper()}"
