from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from app.module.business_types import PurchaseOrderStatus
from app.usecase.policies import line_subtotal, taxed_amount, TaxedAmount


@dataclass(frozen=True)
class PurchaseLine:
    product_id: int
    quantity: int
    unit_cost: Decimal
    minimum_order_quantity: int = 1


@dataclass(frozen=True)
class ReceiptLine:
    purchase_order_item_id: int
    ordered_quantity: int
    previously_received_quantity: int
    accepted_quantity: int
    rejected_quantity: int
    rejection_reason: str | None = None

    @property
    def received_quantity(self) -> int:
        return self.accepted_quantity + self.rejected_quantity

    @property
    def remaining_before_receipt(self) -> int:
        return self.ordered_quantity - self.previously_received_quantity


@dataclass(frozen=True)
class ReorderDecision:
    should_reorder: bool
    available_quantity: int
    recommended_quantity: int
    reason: str


def validate_purchase_lines(lines: Iterable[PurchaseLine]) -> list[PurchaseLine]:
    materialized = list(lines)
    if not materialized:
        raise ValueError("at least one purchase line is required")
    product_ids = [line.product_id for line in materialized]
    if len(product_ids) != len(set(product_ids)):
        raise ValueError("purchase lines must have unique products")
    for line in materialized:
        if line.product_id <= 0:
            raise ValueError("product id must be positive")
        if line.quantity <= 0:
            raise ValueError("quantity must be positive")
        if line.minimum_order_quantity <= 0:
            raise ValueError("minimum order quantity must be positive")
        if line.quantity < line.minimum_order_quantity:
            raise ValueError("quantity is below supplier minimum")
        if line.unit_cost <= 0:
            raise ValueError("unit cost must be positive")
    return materialized


def purchase_totals(lines: Iterable[PurchaseLine]) -> TaxedAmount:
    validated = validate_purchase_lines(lines)
    return taxed_amount(line_subtotal(line.unit_cost, line.quantity) for line in validated)


def validate_receipt_line(line: ReceiptLine) -> None:
    if line.ordered_quantity <= 0:
        raise ValueError("ordered quantity must be positive")
    if line.previously_received_quantity < 0:
        raise ValueError("previously received quantity must not be negative")
    if line.previously_received_quantity > line.ordered_quantity:
        raise ValueError("previously received quantity exceeds order")
    if line.accepted_quantity < 0 or line.rejected_quantity < 0:
        raise ValueError("receipt quantities must not be negative")
    if line.received_quantity <= 0:
        raise ValueError("receipt quantity must be positive")
    if line.received_quantity > line.remaining_before_receipt:
        raise ValueError("receipt quantity exceeds remaining order")
    if line.rejected_quantity and not line.rejection_reason:
        raise ValueError("rejection reason is required")


def purchase_order_status(ordered_and_received: Iterable[tuple[int, int]]) -> str:
    quantities = list(ordered_and_received)
    if not quantities:
        raise ValueError("purchase order must contain lines")
    if any(ordered <= 0 or received < 0 or received > ordered for ordered, received in quantities):
        raise ValueError("invalid purchase order quantities")
    if all(ordered == received for ordered, received in quantities):
        return PurchaseOrderStatus.RECEIVED.value
    if any(received > 0 for _, received in quantities):
        return PurchaseOrderStatus.PARTIALLY_RECEIVED.value
    return PurchaseOrderStatus.APPROVED.value


def reorder_decision(*, on_hand_quantity: int, reserved_quantity: int, reorder_point: int, target_stock_quantity: int, inbound_quantity: int = 0) -> ReorderDecision:
    if min(on_hand_quantity, reserved_quantity, reorder_point, target_stock_quantity, inbound_quantity) < 0:
        raise ValueError("inventory planning quantities must not be negative")
    if reserved_quantity > on_hand_quantity:
        raise ValueError("reserved quantity exceeds on-hand quantity")
    if target_stock_quantity <= reorder_point:
        raise ValueError("target stock must exceed reorder point")
    available = on_hand_quantity - reserved_quantity + inbound_quantity
    should_reorder = available <= reorder_point
    recommended = max(target_stock_quantity - available, 0) if should_reorder else 0
    reason = "BELOW_REORDER_POINT" if available < reorder_point else "AT_REORDER_POINT" if should_reorder else "SUFFICIENT_STOCK"
    return ReorderDecision(should_reorder=should_reorder, available_quantity=available, recommended_quantity=recommended, reason=reason)
