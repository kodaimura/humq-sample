from dataclasses import dataclass
from datetime import date
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
from app.usecase.billing._policies import (
    InvoiceableLine,
    build_invoice_lines,
    invoice_totals,
    validate_invoice_dates,
)
from app.usecase.organizations._operations import RequireOrganizationRoleOperation


@dataclass(frozen=True)
class GenerateInvoiceInput:
    account_id: int
    shipment_id: int
    issue_date: date
    due_date: date


class GenerateInvoiceUsecase:
    def __init__(self, db: Session):
        self.db = db; self.require_role = RequireOrganizationRoleOperation(db); self.shipments = ShipmentModule(db); self.orders = SalesOrderModule(db); self.products = ProductModule(db); self.invoices = InvoiceModule(db); self.items = InvoiceItemModule(db); self.history = InvoiceStatusHistoryModule(db); self.billing = BillingOverviewQuery(db); self.audit = AuditLogModule(db)

    def execute(self, input: GenerateInvoiceInput) -> Invoice:
        shipment = self.shipments.get_by_id(input.shipment_id)
        if not shipment: raise AppError(code=ErrorCode.SHIPMENT_NOT_FOUND)
        order = self.orders.get_by_id(shipment.order_id); assert order is not None
        self.require_role.run(organization_id=order.seller_organization_id, account_id=input.account_id, allowed_roles={MemberRole.ADMIN.value, MemberRole.SALES.value})
        if shipment.status != ShipmentStatus.SHIPPED.value: raise AppError(code=ErrorCode.INVALID_INVOICE_STATE)
        invoiceable = self.billing.invoiceable_shipment_items(shipment.id)
        try:
            validate_invoice_dates(input.issue_date, input.due_date)
            calculated_lines = build_invoice_lines(
                InvoiceableLine(
                    reference_id=line.shipment_item_id,
                    shipped_quantity=line.shipped_quantity,
                    previously_invoiced_quantity=line.invoiced_quantity,
                    unit_price=line.unit_price,
                )
                for line in invoiceable
            )
            totals = invoice_totals(calculated_lines)
        except ValueError as exc:
            raise AppError(code=ErrorCode.INVALID_INVOICE_STATE) from exc
        source_lines = {line.shipment_item_id: line for line in invoiceable}
        invoice = self.invoices.create(invoice_number=_new_invoice_number(), seller_organization_id=order.seller_organization_id, customer_organization_id=order.customer_organization_id, order_id=order.id, issue_date=input.issue_date, due_date=input.due_date, created_by_account_id=input.account_id)
        for amount in calculated_lines:
            source = source_lines[amount.reference_id]
            product = self.products.get_by_id(source.product_id); assert product is not None
            self.items.create(invoice_id=invoice.id, order_item_id=source.order_item_id, shipment_item_id=source.shipment_item_id, product_id=source.product_id, description=product.name, quantity=amount.quantity, unit_price=amount.unit_price, subtotal=amount.subtotal, tax_amount=amount.tax_amount, total_amount=amount.total_amount)
        self.invoices.set_totals(invoice, subtotal=totals.subtotal, tax_amount=totals.tax_amount, total_amount=totals.total_amount)
        self.history.create(invoice_id=invoice.id, from_status=None, to_status=InvoiceStatus.DRAFT.value, reason=None, changed_by_account_id=input.account_id)
        self.audit.record(actor_account_id=input.account_id, action="invoice.generated", resource_type="invoice", resource_id=invoice.id, details={"shipment_id": shipment.id, "total_amount": str(invoice.total_amount)})
        self.db.commit(); return invoice


class IssueInvoiceUsecase:
    def __init__(self, db: Session):
        self.db = db; self.require_role = RequireOrganizationRoleOperation(db); self.invoices = InvoiceModule(db); self.history = InvoiceStatusHistoryModule(db); self.outbox = OutboxEventModule(db); self.audit = AuditLogModule(db)

    def execute(self, *, account_id: int, invoice_id: int, reason: str | None = None) -> Invoice:
        invoice = self.invoices.get_for_update(invoice_id)
        if not invoice: raise AppError(code=ErrorCode.INVOICE_NOT_FOUND)
        self.require_role.run(organization_id=invoice.seller_organization_id, account_id=account_id, allowed_roles={MemberRole.ADMIN.value, MemberRole.SALES.value})
        if invoice.status != InvoiceStatus.DRAFT.value or invoice.paid_amount > 0: raise AppError(code=ErrorCode.INVALID_INVOICE_STATE)
        previous = self.invoices.change_status(invoice, InvoiceStatus.ISSUED.value)
        self.history.create(invoice_id=invoice.id, from_status=previous, to_status=InvoiceStatus.ISSUED.value, reason=reason, changed_by_account_id=account_id)
        self.outbox.enqueue(event_type="invoice.issued", aggregate_type="invoice", aggregate_id=invoice.id, payload={"invoice_id": invoice.id, "status": InvoiceStatus.ISSUED.value, "total_amount": str(invoice.total_amount)})
        self.audit.record(actor_account_id=account_id, action="invoice.issued", resource_type="invoice", resource_id=invoice.id, details={"reason": reason})
        self.db.commit(); return invoice


class VoidInvoiceUsecase:
    def __init__(self, db: Session):
        self.db = db; self.require_role = RequireOrganizationRoleOperation(db); self.invoices = InvoiceModule(db); self.history = InvoiceStatusHistoryModule(db); self.outbox = OutboxEventModule(db); self.audit = AuditLogModule(db)

    def execute(self, *, account_id: int, invoice_id: int, reason: str | None = None) -> Invoice:
        invoice = self.invoices.get_for_update(invoice_id)
        if not invoice: raise AppError(code=ErrorCode.INVOICE_NOT_FOUND)
        self.require_role.run(organization_id=invoice.seller_organization_id, account_id=account_id, allowed_roles={MemberRole.ADMIN.value, MemberRole.SALES.value})
        if invoice.status not in {InvoiceStatus.DRAFT.value, InvoiceStatus.ISSUED.value} or invoice.paid_amount > 0: raise AppError(code=ErrorCode.INVALID_INVOICE_STATE)
        previous = self.invoices.change_status(invoice, InvoiceStatus.VOID.value)
        self.history.create(invoice_id=invoice.id, from_status=previous, to_status=InvoiceStatus.VOID.value, reason=reason, changed_by_account_id=account_id)
        self.outbox.enqueue(event_type="invoice.void", aggregate_type="invoice", aggregate_id=invoice.id, payload={"invoice_id": invoice.id, "status": InvoiceStatus.VOID.value, "total_amount": str(invoice.total_amount)})
        self.audit.record(actor_account_id=account_id, action="invoice.void", resource_type="invoice", resource_id=invoice.id, details={"reason": reason})
        self.db.commit(); return invoice


def _new_invoice_number() -> str:
    return f"INV-{date.today():%Y%m%d}-{secrets.token_hex(3).upper()}"
