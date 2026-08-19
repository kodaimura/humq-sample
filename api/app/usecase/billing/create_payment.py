import secrets
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.error import AppError, ErrorCode
from app.module.audit_log import AuditLogModule
from app.module.business_types import MemberRole
from app.module.organization import OrganizationModule
from app.module.payment import Payment, PaymentModule
from app.usecase.organizations._operations import RequireOrganizationRoleOperation
from app.usecase._transaction import transactional


@dataclass(frozen=True)
class CreatePaymentInput:
    account_id: int
    payee_organization_id: int
    payer_organization_id: int
    payment_date: date
    amount: Decimal
    method: str
    reference: str | None


class CreatePaymentUsecase:
    def __init__(self, db: Session):
        self.db = db
        self.require_role = RequireOrganizationRoleOperation(db)
        self.organizations = OrganizationModule(db)
        self.payments = PaymentModule(db)
        self.audit = AuditLogModule(db)

    @transactional
    def execute(self, input: CreatePaymentInput) -> Payment:
        self.require_role.run(
            organization_id=input.payee_organization_id,
            account_id=input.account_id,
            allowed_roles={MemberRole.ADMIN.value, MemberRole.SALES.value},
        )
        payer = self.organizations.get_by_id(input.payer_organization_id)
        if not payer:
            raise AppError(code=ErrorCode.ORGANIZATION_NOT_FOUND)
        if input.amount <= 0 or input.method not in {
            "BANK_TRANSFER",
            "CARD",
            "CASH",
            "OTHER",
        }:
            raise AppError(code=ErrorCode.INVALID_PAYMENT_STATE)
        payment = self.payments.create(
            payment_number=_new_payment_number(),
            payer_organization_id=payer.id,
            payee_organization_id=input.payee_organization_id,
            payment_date=input.payment_date,
            amount=input.amount,
            unallocated_amount=input.amount,
            method=input.method,
            reference=input.reference,
            created_by_account_id=input.account_id,
        )
        self.audit.record(
            actor_account_id=input.account_id,
            action="payment.created",
            resource_type="payment",
            resource_id=payment.id,
            details={"amount": str(payment.amount), "payer_id": payer.id},
        )
        return payment


def _new_payment_number() -> str:
    return f"PAY-{date.today():%Y%m%d}-{secrets.token_hex(3).upper()}"
