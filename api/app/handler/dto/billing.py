from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class GenerateInvoiceRequest(BaseModel):
    issue_date: date
    due_date: date


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    invoice_number: str
    seller_organization_id: int
    customer_organization_id: int
    order_id: int
    status: str
    issue_date: date
    due_date: date
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    balance_due: Decimal
    issued_at: datetime | None


class InvoiceOperationResponse(BaseModel):
    invoice: InvoiceResponse


class InvoiceStatusRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=1000)


class CreatePaymentRequest(BaseModel):
    payer_organization_id: int
    payment_date: date
    amount: Decimal = Field(gt=0)
    method: str
    reference: str | None = Field(default=None, max_length=100)


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    payment_number: str
    payer_organization_id: int
    payee_organization_id: int
    status: str
    payment_date: date
    amount: Decimal
    unallocated_amount: Decimal
    method: str
    reference: str | None
    posted_at: datetime | None


class PaymentOperationResponse(BaseModel):
    payment: PaymentResponse


class PaymentAllocationRequest(BaseModel):
    invoice_id: int
    amount: Decimal = Field(gt=0)


class PostPaymentRequest(BaseModel):
    allocations: list[PaymentAllocationRequest] = Field(min_length=1)


class ReceivableSummaryResponse(BaseModel):
    customer_organization_id: int
    customer_name: str
    invoice_count: int
    total_invoiced: Decimal
    total_paid: Decimal
    balance_due: Decimal


class ReceivablesResponse(BaseModel):
    receivables: list[ReceivableSummaryResponse]
