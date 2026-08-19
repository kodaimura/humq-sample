from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.error import AppError, ErrorCode
from app.module.audit_log import AuditLogModule
from app.module.business_types import InvoiceStatus, MemberRole, PaymentStatus
from app.module.invoice import Invoice, InvoiceModule
from app.module.invoice_status_history import InvoiceStatusHistoryModule
from app.module.outbox_event import OutboxEventModule
from app.module.payment import Payment, PaymentModule
from app.module.payment_allocation import PaymentAllocationModule
from app.usecase.billing._policies import (
    PaymentAllocationRequest,
    validate_payment_allocations,
)
from app.usecase.organizations._operations import RequireOrganizationRoleOperation


@dataclass(frozen=True)
class PaymentAllocationInput:
    invoice_id: int
    amount: Decimal


class PostPaymentUsecase:
    def __init__(self, db: Session):
        self.db = db
        self.require_role = RequireOrganizationRoleOperation(db)
        self.payments = PaymentModule(db)
        self.allocations = PaymentAllocationModule(db)
        self.invoices = InvoiceModule(db)
        self.history = InvoiceStatusHistoryModule(db)
        self.outbox = OutboxEventModule(db)
        self.audit = AuditLogModule(db)

    def execute(
        self,
        *,
        account_id: int,
        payment_id: int,
        allocations: list[PaymentAllocationInput],
    ) -> Payment:
        payment = self.payments.get_for_update(payment_id)
        if not payment:
            raise AppError(code=ErrorCode.PAYMENT_NOT_FOUND)
        self.require_role.run(
            organization_id=payment.payee_organization_id,
            account_id=account_id,
            allowed_roles={MemberRole.ADMIN.value, MemberRole.SALES.value},
        )
        if payment.status != PaymentStatus.DRAFT.value:
            raise AppError(code=ErrorCode.INVALID_PAYMENT_STATE)
        resolved_allocations: list[tuple[PaymentAllocationInput, Invoice]] = []
        for requested in allocations:
            invoice = self.invoices.get_for_update(requested.invoice_id)
            if (
                not invoice
                or invoice.seller_organization_id != payment.payee_organization_id
                or invoice.customer_organization_id != payment.payer_organization_id
            ):
                raise AppError(code=ErrorCode.INVOICE_NOT_FOUND)
            if invoice.status not in {
                InvoiceStatus.ISSUED.value,
                InvoiceStatus.PARTIALLY_PAID.value,
            }:
                raise AppError(code=ErrorCode.PAYMENT_ALLOCATION_EXCEEDED)
            resolved_allocations.append((requested, invoice))
        try:
            validate_payment_allocations(
                payment.amount,
                (
                    PaymentAllocationRequest(
                        invoice_id=invoice.id,
                        invoice_balance=invoice.balance_due,
                        allocation_amount=requested.amount,
                    )
                    for requested, invoice in resolved_allocations
                ),
            )
        except ValueError as exc:
            raise AppError(code=ErrorCode.PAYMENT_ALLOCATION_EXCEEDED) from exc
        for requested, invoice in resolved_allocations:
            if not self.payments.allocate(payment, requested.amount):
                raise AppError(code=ErrorCode.PAYMENT_ALLOCATION_EXCEEDED)
            previous = self.invoices.apply_payment(invoice, requested.amount)
            self.allocations.create(
                payment_id=payment.id,
                invoice_id=invoice.id,
                amount=requested.amount,
                allocated_by_account_id=account_id,
            )
            self.history.create(
                invoice_id=invoice.id,
                from_status=previous,
                to_status=invoice.status,
                reason=f"Payment {payment.payment_number}",
                changed_by_account_id=account_id,
            )
        self.payments.post(payment)
        self.outbox.enqueue(
            event_type="payment.posted",
            aggregate_type="payment",
            aggregate_id=payment.id,
            payload={
                "payment_id": payment.id,
                "amount": str(payment.amount),
                "unallocated_amount": str(payment.unallocated_amount),
            },
        )
        self.audit.record(
            actor_account_id=account_id,
            action="payment.posted",
            resource_type="payment",
            resource_id=payment.id,
            details={
                "allocation_count": len(allocations),
                "unallocated_amount": str(payment.unallocated_amount),
            },
        )
        self.db.commit()
        return payment
