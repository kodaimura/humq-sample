import unittest
from decimal import Decimal

from app.core.error import AppError
from app.usecase._policies import line_subtotal, money, prorate_amount, resolve_login_id, sum_money, tax_for, taxed_amount, total_with_tax


class SharedPolicyTest(unittest.TestCase):
    def test_login_id_policy_uses_configured_identifier(self):
        self.assertEqual(
            resolve_login_id(None, "user@example.com", login_id_mode="email"),
            "user@example.com",
        )
        self.assertEqual(
            resolve_login_id("user-1", None, login_id_mode="login_id"),
            "user-1",
        )

    def test_login_id_policy_requires_the_configured_identifier(self):
        with self.assertRaises(AppError):
            resolve_login_id(None, None, login_id_mode="email")
        with self.assertRaises(AppError):
            resolve_login_id(None, None, login_id_mode="login_id")

    def test_login_id_policy_rejects_unknown_mode(self):
        with self.assertRaises(AppError):
            resolve_login_id("user-1", None, login_id_mode="unknown")


class MoneyPolicyTest(unittest.TestCase):
    def test_money_uses_half_up_rounding(self):
        self.assertEqual(money("1.005"), Decimal("1.01"))
        self.assertEqual(money("1.004"), Decimal("1.00"))

    def test_line_subtotal_multiplies_and_normalizes(self):
        self.assertEqual(line_subtotal(Decimal("12.345"), 3), Decimal("37.04"))

    def test_line_subtotal_rejects_invalid_values(self):
        with self.assertRaises(ValueError):
            line_subtotal(Decimal("-1"), 1)
        with self.assertRaises(ValueError):
            line_subtotal(Decimal("1"), 0)

    def test_tax_for_uses_default_rate(self):
        self.assertEqual(tax_for(Decimal("100.00")), Decimal("10.00"))
        self.assertEqual(total_with_tax(Decimal("100.00")), Decimal("110.00"))

    def test_tax_for_rejects_invalid_rate(self):
        with self.assertRaises(ValueError):
            tax_for(Decimal("100"), Decimal("1.01"))
        with self.assertRaises(ValueError):
            tax_for(Decimal("-1"))

    def test_sum_money_starts_at_zero(self):
        self.assertEqual(sum_money([]), Decimal("0.00"))
        self.assertEqual(
            sum_money([Decimal("1.111"), Decimal("2.222")]),
            Decimal("3.33"),
        )

    def test_taxed_amount_returns_all_components(self):
        result = taxed_amount([Decimal("100"), Decimal("50")])
        self.assertEqual(result.subtotal, Decimal("150.00"))
        self.assertEqual(result.tax_amount, Decimal("15.00"))
        self.assertEqual(result.total_amount, Decimal("165.00"))

    def test_proration_preserves_total(self):
        allocations = prorate_amount(Decimal("10.00"), [1, 1, 1])
        self.assertEqual(allocations, [Decimal("3.33"), Decimal("3.33"), Decimal("3.34")])
        self.assertEqual(sum(allocations), Decimal("10.00"))

    def test_proration_supports_zero_weight(self):
        self.assertEqual(prorate_amount(Decimal("10.00"), [0, 1]), [Decimal("0.00"), Decimal("10.00")])

    def test_proration_rejects_invalid_weights(self):
        for weights in ([], [0, 0], [-1, 2]):
            with self.subTest(weights=weights), self.assertRaises(ValueError):
                prorate_amount(Decimal("10.00"), weights)


if __name__ == "__main__":
    unittest.main()
