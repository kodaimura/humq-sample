import unittest
from decimal import Decimal

from app.module.business_types import PurchaseOrderStatus
from app.usecase.procurement._policies import (
    PurchaseLine,
    ReceiptLine,
    purchase_order_status,
    purchase_totals,
    reorder_decision,
    validate_purchase_lines,
    validate_receipt_line,
)


class ProcurementPolicyTest(unittest.TestCase):
    def test_purchase_totals_include_tax(self):
        result = purchase_totals(
            [
                PurchaseLine(product_id=1, quantity=2, unit_cost=Decimal("100.00")),
                PurchaseLine(product_id=2, quantity=3, unit_cost=Decimal("50.00")),
            ]
        )
        self.assertEqual(result.subtotal, Decimal("350.00"))
        self.assertEqual(result.tax_amount, Decimal("35.00"))
        self.assertEqual(result.total_amount, Decimal("385.00"))

    def test_purchase_line_honors_supplier_minimum(self):
        with self.assertRaisesRegex(ValueError, "supplier minimum"):
            validate_purchase_lines(
                [
                    PurchaseLine(
                        product_id=1,
                        quantity=4,
                        unit_cost=Decimal("1"),
                        minimum_order_quantity=5,
                    )
                ]
            )

    def test_purchase_lines_must_be_unique(self):
        with self.assertRaisesRegex(ValueError, "unique products"):
            validate_purchase_lines(
                [
                    PurchaseLine(product_id=1, quantity=1, unit_cost=Decimal("1")),
                    PurchaseLine(product_id=1, quantity=1, unit_cost=Decimal("1")),
                ]
            )

    def test_purchase_lines_must_not_be_empty(self):
        with self.assertRaises(ValueError):
            validate_purchase_lines([])

    def test_receipt_accepts_combined_accepted_and_rejected(self):
        validate_receipt_line(
            ReceiptLine(
                purchase_order_item_id=1,
                ordered_quantity=10,
                previously_received_quantity=2,
                accepted_quantity=6,
                rejected_quantity=2,
                rejection_reason="Damaged",
            )
        )

    def test_receipt_rejects_over_receipt(self):
        with self.assertRaisesRegex(ValueError, "exceeds remaining"):
            validate_receipt_line(
                ReceiptLine(
                    purchase_order_item_id=1,
                    ordered_quantity=10,
                    previously_received_quantity=8,
                    accepted_quantity=3,
                    rejected_quantity=0,
                )
            )

    def test_receipt_requires_rejection_reason(self):
        with self.assertRaisesRegex(ValueError, "reason"):
            validate_receipt_line(
                ReceiptLine(
                    purchase_order_item_id=1,
                    ordered_quantity=10,
                    previously_received_quantity=0,
                    accepted_quantity=9,
                    rejected_quantity=1,
                )
            )

    def test_purchase_order_status_is_approved_before_receipt(self):
        self.assertEqual(
            purchase_order_status([(10, 0), (5, 0)]), PurchaseOrderStatus.APPROVED.value
        )

    def test_purchase_order_status_is_partial(self):
        self.assertEqual(
            purchase_order_status([(10, 2), (5, 0)]),
            PurchaseOrderStatus.PARTIALLY_RECEIVED.value,
        )

    def test_purchase_order_status_is_received(self):
        self.assertEqual(
            purchase_order_status([(10, 10), (5, 5)]),
            PurchaseOrderStatus.RECEIVED.value,
        )

    def test_purchase_order_status_rejects_invalid_quantities(self):
        with self.assertRaises(ValueError):
            purchase_order_status([(10, 11)])

    def test_reorder_below_point_targets_stock(self):
        result = reorder_decision(
            on_hand_quantity=6,
            reserved_quantity=2,
            reorder_point=5,
            target_stock_quantity=20,
        )
        self.assertTrue(result.should_reorder)
        self.assertEqual(result.available_quantity, 4)
        self.assertEqual(result.recommended_quantity, 16)
        self.assertEqual(result.reason, "BELOW_REORDER_POINT")

    def test_reorder_at_point_is_triggered(self):
        result = reorder_decision(
            on_hand_quantity=5,
            reserved_quantity=0,
            reorder_point=5,
            target_stock_quantity=20,
        )
        self.assertTrue(result.should_reorder)
        self.assertEqual(result.reason, "AT_REORDER_POINT")

    def test_reorder_considers_inbound_stock(self):
        result = reorder_decision(
            on_hand_quantity=4,
            reserved_quantity=0,
            inbound_quantity=10,
            reorder_point=5,
            target_stock_quantity=20,
        )
        self.assertFalse(result.should_reorder)
        self.assertEqual(result.recommended_quantity, 0)


if __name__ == "__main__":
    unittest.main()
