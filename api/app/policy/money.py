from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable


MONEY_QUANTUM = Decimal("0.01")
DEFAULT_TAX_RATE = Decimal("0.10")


def money(value: Decimal | int | str) -> Decimal:
    """Normalize monetary values at the boundary of a business calculation."""
    return Decimal(value).quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


def line_subtotal(unit_price: Decimal, quantity: int) -> Decimal:
    if unit_price < 0:
        raise ValueError("unit price must not be negative")
    if quantity <= 0:
        raise ValueError("quantity must be positive")
    return money(unit_price * quantity)


def tax_for(subtotal: Decimal, tax_rate: Decimal = DEFAULT_TAX_RATE) -> Decimal:
    if subtotal < 0:
        raise ValueError("subtotal must not be negative")
    if tax_rate < 0 or tax_rate > 1:
        raise ValueError("tax rate must be between zero and one")
    return money(subtotal * tax_rate)


def total_with_tax(subtotal: Decimal, tax_rate: Decimal = DEFAULT_TAX_RATE) -> Decimal:
    normalized = money(subtotal)
    return normalized + tax_for(normalized, tax_rate)


def sum_money(values: Iterable[Decimal]) -> Decimal:
    return money(sum(values, Decimal("0.00")))


@dataclass(frozen=True)
class TaxedAmount:
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal


def taxed_amount(subtotals: Iterable[Decimal], tax_rate: Decimal = DEFAULT_TAX_RATE) -> TaxedAmount:
    subtotal = sum_money(subtotals)
    tax_amount = tax_for(subtotal, tax_rate)
    return TaxedAmount(
        subtotal=subtotal,
        tax_amount=tax_amount,
        total_amount=subtotal + tax_amount,
    )


def prorate_amount(total: Decimal, weights: list[int]) -> list[Decimal]:
    """Split an amount without losing cents; the final line absorbs rounding."""
    normalized = money(total)
    if normalized < 0:
        raise ValueError("total must not be negative")
    if not weights or any(weight < 0 for weight in weights) or sum(weights) <= 0:
        raise ValueError("weights must include a positive value")
    weight_total = Decimal(sum(weights))
    remaining = normalized
    allocations: list[Decimal] = []
    for index, weight in enumerate(weights):
        if index == len(weights) - 1:
            allocation = remaining
        else:
            allocation = money(normalized * Decimal(weight) / weight_total)
            remaining -= allocation
        allocations.append(allocation)
    return allocations
