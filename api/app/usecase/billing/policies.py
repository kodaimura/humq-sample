from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Iterable

from app.usecase.policies import line_subtotal, tax_for, sum_money, TaxedAmount


@dataclass(frozen=True)
class InvoiceableLine:
    reference_id: int
    shipped_quantity: int
    previously_invoiced_quantity: int
    unit_price: Decimal

    @property
    def invoiceable_quantity(self) -> int:
        return max(self.shipped_quantity - self.previously_invoiced_quantity, 0)


@dataclass(frozen=True)
class InvoiceLineAmount:
    reference_id: int
    quantity: int
    unit_price: Decimal
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal


@dataclass(frozen=True)
class PaymentAllocationRequest:
    invoice_id: int
    invoice_balance: Decimal
    allocation_amount: Decimal


def validate_invoice_dates(issue_date: date, due_date: date) -> None:
    if due_date < issue_date:
        raise ValueError("invoice due date must not precede issue date")


def build_invoice_lines(lines: Iterable[InvoiceableLine]) -> list[InvoiceLineAmount]:
    results: list[InvoiceLineAmount] = []
    references: set[int] = set()
    for line in lines:
        if line.reference_id in references:
            raise ValueError("invoice references must be unique")
        references.add(line.reference_id)
        if line.shipped_quantity <= 0:
            raise ValueError("shipped quantity must be positive")
        if line.previously_invoiced_quantity < 0 or line.previously_invoiced_quantity > line.shipped_quantity:
            raise ValueError("invalid previously invoiced quantity")
        if line.unit_price < 0:
            raise ValueError("unit price must not be negative")
        quantity = line.invoiceable_quantity
        if quantity == 0:
            continue
        subtotal = line_subtotal(line.unit_price, quantity)
        tax_amount = tax_for(subtotal)
        results.append(InvoiceLineAmount(reference_id=line.reference_id, quantity=quantity, unit_price=line.unit_price, subtotal=subtotal, tax_amount=tax_amount, total_amount=subtotal + tax_amount))
    if not results:
        raise ValueError("shipment has no invoiceable quantity")
    return results


def invoice_totals(lines: Iterable[InvoiceLineAmount]) -> TaxedAmount:
    materialized = list(lines)
    if not materialized:
        raise ValueError("invoice must contain lines")
    subtotal = sum_money(line.subtotal for line in materialized)
    tax_amount = sum_money(line.tax_amount for line in materialized)
    return TaxedAmount(subtotal=subtotal, tax_amount=tax_amount, total_amount=subtotal + tax_amount)


def validate_payment_allocations(payment_amount: Decimal, allocations: Iterable[PaymentAllocationRequest]) -> Decimal:
    materialized = list(allocations)
    if payment_amount <= 0:
        raise ValueError("payment amount must be positive")
    if not materialized:
        raise ValueError("payment requires allocations")
    invoice_ids = [allocation.invoice_id for allocation in materialized]
    if len(invoice_ids) != len(set(invoice_ids)):
        raise ValueError("an invoice may only be allocated once per payment")
    for allocation in materialized:
        if allocation.invoice_balance <= 0:
            raise ValueError("invoice has no balance")
        if allocation.allocation_amount <= 0:
            raise ValueError("allocation amount must be positive")
        if allocation.allocation_amount > allocation.invoice_balance:
            raise ValueError("allocation exceeds invoice balance")
    allocated = sum_money(allocation.allocation_amount for allocation in materialized)
    if allocated > payment_amount:
        raise ValueError("allocations exceed payment amount")
    return payment_amount - allocated
