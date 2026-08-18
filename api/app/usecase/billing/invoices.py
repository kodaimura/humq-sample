from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
import secrets

from sqlalchemy.orm import Session

from app.core.error import AppError, ErrorCode
from app.module.audit_log import AuditLogModule
from app.module.business_types import InvoiceStatus, MemberRole, ShipmentStatus
from app.module.invoice import Invoice, InvoiceModule
from app.module.invoice_item import InvoiceItemModule
from app.module.invoice_status_history import InvoiceStatusHistoryModule
from app.module.outbox_event import OutboxEventModule
from app.module.product import ProductModule
from app.module.sales_order import SalesOrderModule
from app.module.shipment import ShipmentModule
from app.query.billing_overview import BillingOverviewQuery
from app.usecase.organizations.require_role import RequireOrganizationRoleUsecase


@dataclass(frozen=True)
class GenerateInvoiceInput:
    account_id: int
    shipment_id: int
    issue_date: date
    due_date: date


class GenerateInvoiceUsecase:
    def __init__(self, db: Session):
        self.db = db; self.require_role = RequireOrganizationRoleUsecase(db); self.shipments = ShipmentModule(db); self.orders = SalesOrderModule(db); self.products = ProductModule(db); self.invoices = InvoiceModule(db); self.items = InvoiceItemModule(db); self.history = InvoiceStatusHistoryModule(db); self.billing = BillingOverviewQuery(db); self.audit = AuditLogModule(db)

    def execute(self, input: GenerateInvoiceInput) -> Invoice:
        shipment = self.shipments.get_by_id(input.shipment_id)
        if not shipment: raise AppError(code=ErrorCode.SHIPMENT_NOT_FOUND)
        order = self.orders.get_by_id(shipment.order_id); assert order is not None
        self.require_role.execute(organization_id=order.seller_organization_id, account_id=input.account_id, allowed_roles={MemberRole.ADMIN.value, MemberRole.SALES.value})
        if shipment.status != ShipmentStatus.SHIPPED.value or input.due_date < input.issue_date: raise AppError(code=ErrorCode.INVALID_INVOICE_STATE)
        invoiceable = [line for line in self.billing.invoiceable_shipment_items(shipment.id) if line.invoiceable_quantity > 0]
        if not invoiceable: raise AppError(code=ErrorCode.INVALID_INVOICE_STATE)
        invoice = self.invoices.create(invoice_number=_new_invoice_number(), seller_organization_id=order.seller_organization_id, customer_organization_id=order.customer_organization_id, order_id=order.id, issue_date=input.issue_date, due_date=input.due_date, created_by_account_id=input.account_id)
        subtotal = Decimal("0.00"); tax_total = Decimal("0.00")
        for line in invoiceable:
            product = self.products.get_by_id(line.product_id); assert product is not None
            line_subtotal = (line.unit_price * line.invoiceable_quantity).quantize(Decimal("0.01"))
            tax = (line_subtotal * Decimal("0.10")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            self.items.create(invoice_id=invoice.id, order_item_id=line.order_item_id, shipment_item_id=line.shipment_item_id, product_id=line.product_id, description=product.name, quantity=line.invoiceable_quantity, unit_price=line.unit_price, subtotal=line_subtotal, tax_amount=tax, total_amount=line_subtotal + tax)
            subtotal += line_subtotal; tax_total += tax
        self.invoices.set_totals(invoice, subtotal=subtotal, tax_amount=tax_total, total_amount=subtotal + tax_total)
        self.history.create(invoice_id=invoice.id, from_status=None, to_status=InvoiceStatus.DRAFT.value, reason=None, changed_by_account_id=input.account_id)
        self.audit.record(actor_account_id=input.account_id, action="invoice.generated", resource_type="invoice", resource_id=invoice.id, details={"shipment_id": shipment.id, "total_amount": str(invoice.total_amount)})
        self.db.commit(); return invoice


class ChangeInvoiceStatusUsecase:
    def __init__(self, db: Session):
        self.db = db; self.require_role = RequireOrganizationRoleUsecase(db); self.invoices = InvoiceModule(db); self.history = InvoiceStatusHistoryModule(db); self.outbox = OutboxEventModule(db); self.audit = AuditLogModule(db)

    def execute(self, *, account_id: int, invoice_id: int, action: str, reason: str | None = None) -> Invoice:
        invoice = self.invoices.get_for_update(invoice_id)
        if not invoice: raise AppError(code=ErrorCode.INVOICE_NOT_FOUND)
        self.require_role.execute(organization_id=invoice.seller_organization_id, account_id=account_id, allowed_roles={MemberRole.ADMIN.value, MemberRole.SALES.value})
        transitions = {"issue": ({InvoiceStatus.DRAFT.value}, InvoiceStatus.ISSUED.value), "void": ({InvoiceStatus.DRAFT.value, InvoiceStatus.ISSUED.value}, InvoiceStatus.VOID.value)}
        allowed, target = transitions.get(action, (set(), ""))
        if invoice.status not in allowed or invoice.paid_amount > 0: raise AppError(code=ErrorCode.INVALID_INVOICE_STATE)
        previous = self.invoices.change_status(invoice, target)
        self.history.create(invoice_id=invoice.id, from_status=previous, to_status=target, reason=reason, changed_by_account_id=account_id)
        self.outbox.enqueue(event_type=f"invoice.{target.lower()}", aggregate_type="invoice", aggregate_id=invoice.id, payload={"invoice_id": invoice.id, "status": target, "total_amount": str(invoice.total_amount)})
        self.audit.record(actor_account_id=account_id, action=f"invoice.{target.lower()}", resource_type="invoice", resource_id=invoice.id, details={"reason": reason})
        self.db.commit(); return invoice


def _new_invoice_number() -> str:
    return f"INV-{date.today():%Y%m%d}-{secrets.token_hex(3).upper()}"
