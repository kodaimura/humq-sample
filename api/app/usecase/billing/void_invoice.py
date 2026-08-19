from sqlalchemy.orm import Session

from app.core.error import AppError, ErrorCode
from app.module.audit_log import AuditLogModule
from app.module.business_types import InvoiceStatus, MemberRole
from app.module.invoice import Invoice, InvoiceModule
from app.module.invoice_status_history import InvoiceStatusHistoryModule
from app.module.outbox_event import OutboxEventModule
from app.usecase.organizations._operations import RequireOrganizationRoleOperation


class VoidInvoiceUsecase:
    def __init__(self, db: Session):
        self.db = db
        self.require_role = RequireOrganizationRoleOperation(db)
        self.invoices = InvoiceModule(db)
        self.history = InvoiceStatusHistoryModule(db)
        self.outbox = OutboxEventModule(db)
        self.audit = AuditLogModule(db)

    def execute(
        self, *, account_id: int, invoice_id: int, reason: str | None = None
    ) -> Invoice:
        invoice = self.invoices.get_for_update(invoice_id)
        if not invoice:
            raise AppError(code=ErrorCode.INVOICE_NOT_FOUND)
        self.require_role.run(
            organization_id=invoice.seller_organization_id,
            account_id=account_id,
            allowed_roles={MemberRole.ADMIN.value, MemberRole.SALES.value},
        )
        if (
            invoice.status
            not in {InvoiceStatus.DRAFT.value, InvoiceStatus.ISSUED.value}
            or invoice.paid_amount > 0
        ):
            raise AppError(code=ErrorCode.INVALID_INVOICE_STATE)
        previous = self.invoices.change_status(invoice, InvoiceStatus.VOID.value)
        self.history.create(
            invoice_id=invoice.id,
            from_status=previous,
            to_status=InvoiceStatus.VOID.value,
            reason=reason,
            changed_by_account_id=account_id,
        )
        self.outbox.enqueue(
            event_type="invoice.void",
            aggregate_type="invoice",
            aggregate_id=invoice.id,
            payload={
                "invoice_id": invoice.id,
                "status": InvoiceStatus.VOID.value,
                "total_amount": str(invoice.total_amount),
            },
        )
        self.audit.record(
            actor_account_id=account_id,
            action="invoice.void",
            resource_type="invoice",
            resource_id=invoice.id,
            details={"reason": reason},
        )
        self.db.commit()
        return invoice
