import unittest
from datetime import date
from decimal import Decimal

from app.module.business_types import InvoiceStatus, ReturnDisposition, SalesReturnStatus
from app.policy.billing import InvoiceableLine, PaymentAllocationRequest, build_invoice_lines, invoice_status_after_payment, invoice_totals, validate_invoice_dates, validate_payment_allocations
from app.policy.returns import ReturnEligibility, ReturnReceiptDisposition, ReturnRequestLine, net_restock_quantity, requested_credit, return_status, validate_return_disposition, validate_return_request


class ReturnsPolicyTest(unittest.TestCase):
    def test_return_eligibility_subtracts_prior_requests(self):
        eligibility = ReturnEligibility(shipped_quantity=10, previously_requested_quantity=3)
        self.assertEqual(eligibility.returnable_quantity, 7)

    def test_return_eligibility_never_goes_negative(self):
        self.assertEqual(ReturnEligibility(2, 3).returnable_quantity, 0)

    def test_requested_credit_totals_lines(self):
        result = requested_credit([
            ReturnRequestLine(order_item_id=1, requested_quantity=2, eligibility=ReturnEligibility(5, 0), unit_credit=Decimal("100")),
            ReturnRequestLine(order_item_id=2, requested_quantity=1, eligibility=ReturnEligibility(1, 0), unit_credit=Decimal("50")),
        ])
        self.assertEqual(result, Decimal("250.00"))

    def test_return_request_cannot_exceed_eligibility(self):
        with self.assertRaises(ValueError):
            validate_return_request([ReturnRequestLine(order_item_id=1, requested_quantity=3, eligibility=ReturnEligibility(2, 0), unit_credit=Decimal("1"))])

    def test_return_request_items_are_unique(self):
        line = ReturnRequestLine(order_item_id=1, requested_quantity=1, eligibility=ReturnEligibility(2, 0), unit_credit=Decimal("1"))
        with self.assertRaises(ValueError):
            validate_return_request([line, line])

    def test_return_disposition_splits_restock_and_discard(self):
        restock = ReturnReceiptDisposition(2, ReturnDisposition.RESTOCK.value)
        discard = ReturnReceiptDisposition(3, ReturnDisposition.DISCARD.value)
        self.assertEqual(restock.restocked_quantity, 2)
        self.assertEqual(restock.discarded_quantity, 0)
        self.assertEqual(discard.discarded_quantity, 3)
        self.assertEqual(net_restock_quantity([restock, discard]), 2)

    def test_return_disposition_rejects_unknown_value(self):
        with self.assertRaises(ValueError):
            validate_return_disposition(ReturnReceiptDisposition(1, "UNKNOWN"))

    def test_return_status_progression(self):
        self.assertEqual(return_status([(3, 0)]), SalesReturnStatus.APPROVED.value)
        self.assertEqual(return_status([(3, 2)]), SalesReturnStatus.PARTIALLY_RECEIVED.value)
        self.assertEqual(return_status([(3, 3)]), SalesReturnStatus.COMPLETED.value)


class BillingPolicyTest(unittest.TestCase):
    def test_invoice_dates_require_due_date_after_issue(self):
        validate_invoice_dates(date(2026, 1, 1), date(2026, 1, 31))
        with self.assertRaises(ValueError):
            validate_invoice_dates(date(2026, 2, 1), date(2026, 1, 31))

    def test_invoice_lines_only_include_uninvoiced_quantity(self):
        lines = build_invoice_lines([InvoiceableLine(reference_id=1, shipped_quantity=5, previously_invoiced_quantity=2, unit_price=Decimal("100"))])
        self.assertEqual(lines[0].quantity, 3)
        self.assertEqual(lines[0].subtotal, Decimal("300.00"))
        self.assertEqual(lines[0].tax_amount, Decimal("30.00"))

    def test_invoice_lines_reject_fully_invoiced_shipment(self):
        with self.assertRaises(ValueError):
            build_invoice_lines([InvoiceableLine(reference_id=1, shipped_quantity=5, previously_invoiced_quantity=5, unit_price=Decimal("100"))])

    def test_invoice_lines_reject_duplicate_references(self):
        with self.assertRaises(ValueError):
            build_invoice_lines([
                InvoiceableLine(reference_id=1, shipped_quantity=1, previously_invoiced_quantity=0, unit_price=Decimal("1")),
                InvoiceableLine(reference_id=1, shipped_quantity=1, previously_invoiced_quantity=0, unit_price=Decimal("1")),
            ])

    def test_invoice_totals_sum_line_level_tax(self):
        lines = build_invoice_lines([
            InvoiceableLine(reference_id=1, shipped_quantity=2, previously_invoiced_quantity=0, unit_price=Decimal("100")),
            InvoiceableLine(reference_id=2, shipped_quantity=1, previously_invoiced_quantity=0, unit_price=Decimal("50")),
        ])
        totals = invoice_totals(lines)
        self.assertEqual(totals.subtotal, Decimal("250.00"))
        self.assertEqual(totals.tax_amount, Decimal("25.00"))
        self.assertEqual(totals.total_amount, Decimal("275.00"))

    def test_payment_allocations_leave_unallocated_cash(self):
        remainder = validate_payment_allocations(Decimal("100"), [PaymentAllocationRequest(invoice_id=1, invoice_balance=Decimal("80"), allocation_amount=Decimal("60"))])
        self.assertEqual(remainder, Decimal("40.00"))

    def test_payment_allocation_cannot_exceed_invoice(self):
        with self.assertRaises(ValueError):
            validate_payment_allocations(Decimal("100"), [PaymentAllocationRequest(invoice_id=1, invoice_balance=Decimal("50"), allocation_amount=Decimal("60"))])

    def test_payment_allocations_require_unique_invoices(self):
        allocation = PaymentAllocationRequest(invoice_id=1, invoice_balance=Decimal("50"), allocation_amount=Decimal("20"))
        with self.assertRaises(ValueError):
            validate_payment_allocations(Decimal("100"), [allocation, allocation])

    def test_invoice_status_follows_paid_amount(self):
        total = Decimal("100")
        self.assertEqual(invoice_status_after_payment(total, Decimal("0")), InvoiceStatus.ISSUED.value)
        self.assertEqual(invoice_status_after_payment(total, Decimal("50")), InvoiceStatus.PARTIALLY_PAID.value)
        self.assertEqual(invoice_status_after_payment(total, Decimal("100")), InvoiceStatus.PAID.value)

    def test_invoice_status_rejects_overpayment(self):
        with self.assertRaises(ValueError):
            invoice_status_after_payment(Decimal("100"), Decimal("101"))


if __name__ == "__main__":
    unittest.main()
