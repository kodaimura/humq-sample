from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from app.module.business_types import ReturnDisposition, SalesReturnStatus
from app.usecase._policies import line_subtotal, sum_money


@dataclass(frozen=True)
class ReturnEligibility:
    shipped_quantity: int
    previously_requested_quantity: int

    @property
    def returnable_quantity(self) -> int:
        return max(self.shipped_quantity - self.previously_requested_quantity, 0)


@dataclass(frozen=True)
class ReturnRequestLine:
    order_item_id: int
    requested_quantity: int
    eligibility: ReturnEligibility
    unit_credit: Decimal


@dataclass(frozen=True)
class ReturnReceiptDisposition:
    quantity: int
    disposition: str

    @property
    def restocked_quantity(self) -> int:
        return (
            self.quantity if self.disposition == ReturnDisposition.RESTOCK.value else 0
        )

    @property
    def discarded_quantity(self) -> int:
        return (
            self.quantity if self.disposition == ReturnDisposition.DISCARD.value else 0
        )


def validate_return_request(
    lines: Iterable[ReturnRequestLine],
) -> list[ReturnRequestLine]:
    materialized = list(lines)
    if not materialized:
        raise ValueError("at least one return line is required")
    order_item_ids = [line.order_item_id for line in materialized]
    if len(order_item_ids) != len(set(order_item_ids)):
        raise ValueError("return lines must have unique order items")
    for line in materialized:
        if line.requested_quantity <= 0:
            raise ValueError("requested return quantity must be positive")
        if line.requested_quantity > line.eligibility.returnable_quantity:
            raise ValueError("requested return quantity exceeds shipped quantity")
        if line.unit_credit < 0:
            raise ValueError("unit credit must not be negative")
    return materialized


def requested_credit(lines: Iterable[ReturnRequestLine]) -> Decimal:
    validated = validate_return_request(lines)
    return sum_money(
        line_subtotal(line.unit_credit, line.requested_quantity) for line in validated
    )


def validate_return_disposition(disposition: ReturnReceiptDisposition) -> None:
    if disposition.quantity <= 0:
        raise ValueError("return receipt quantity must be positive")
    if disposition.disposition not in {
        ReturnDisposition.RESTOCK.value,
        ReturnDisposition.DISCARD.value,
    }:
        raise ValueError("unknown return disposition")


def return_status(requested_and_received: Iterable[tuple[int, int]]) -> str:
    quantities = list(requested_and_received)
    if not quantities:
        raise ValueError("sales return must contain lines")
    if any(
        requested <= 0 or received < 0 or received > requested
        for requested, received in quantities
    ):
        raise ValueError("invalid return quantities")
    if all(requested == received for requested, received in quantities):
        return SalesReturnStatus.COMPLETED.value
    if any(received > 0 for _, received in quantities):
        return SalesReturnStatus.PARTIALLY_RECEIVED.value
    return SalesReturnStatus.APPROVED.value


def net_restock_quantity(dispositions: Iterable[ReturnReceiptDisposition]) -> int:
    materialized = list(dispositions)
    for disposition in materialized:
        validate_return_disposition(disposition)
    return sum(disposition.restocked_quantity for disposition in materialized)
