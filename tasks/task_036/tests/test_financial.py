"""Tests for the financial calculator modules."""

import sys
import os
import pytest
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.money import Money
from src.ledger import Ledger
from src.tax import TaxCalculator


# ── pass-to-pass: these must always pass ─────────────────────────────────

class TestMoneyBasicOperations:
    """Basic Money operations that work correctly regardless of precision."""

    def test_money_basic_operations(self):
        m1 = Money(100, "USD")
        m2 = Money(50, "USD")
        result = m1 + m2
        # Whole-dollar addition is fine even with floats
        assert str(result) == "$150.00"

        m3 = m1 - m2
        assert str(m3) == "$50.00"

        assert m1.currency == "USD"
        assert not m1.is_negative()
        assert Money.zero("USD").is_zero()

        with pytest.raises(ValueError):
            Money(10, "USD") + Money(10, "EUR")

        with pytest.raises(ValueError):
            Money(10, "XXX")


class TestLedgerAddTransaction:
    """Basic ledger operations."""

    def test_ledger_add_transaction(self):
        ledger = Ledger("test_account")
        ledger.add_transaction("Sale", Money(100, "USD"), category="sales")
        ledger.add_transaction("Refund", Money(-20, "USD"), category="sales")

        assert ledger.transaction_count == 2
        assert len(ledger.get_transactions("sales")) == 2
        assert len(ledger.get_transactions("other")) == 0

        txn = ledger.get_transactions()[0]
        assert txn.description == "Sale"
        assert not txn.is_posted

        ledger.post_all()
        assert txn.is_posted


class TestTaxRateLookup:
    """Tax rate lookup functionality."""

    def test_tax_rate_lookup(self):
        from src.tax import TaxBracket

        brackets = [
            TaxBracket("low", 0.05, 0, 1000),
            TaxBracket("mid", 0.10, 1000, 5000),
            TaxBracket("high", 0.20, 5000),
        ]
        calc = TaxCalculator(brackets=brackets)

        assert calc.get_rate_for_amount(500) == 0.05
        assert calc.get_rate_for_amount(3000) == 0.10
        assert calc.get_rate_for_amount(10000) == 0.20


# ── fail-to-pass: these FAIL with the bug, PASS after fix ────────────────

class TestTaxPrecision:
    """Tax calculations must be exact to the penny."""

    @pytest.mark.fail_to_pass
    def test_tax_calculation_precision(self):
        """Tax calculations must be exact to the penny with no float drift."""
        calc = TaxCalculator(rate=0.1)

        # $0.05 at 10% = $0.005 exactly. But float gives 0.005000000000000001
        price = Money(0.05, "USD")
        tax = calc.calculate_tax(price)
        assert tax.amount == 0.005, (
            f"Tax on $0.05 at 10% should be exactly 0.005, got {tax.amount!r}"
        )

        # $1.10 + $2.20 should be exactly $3.30
        m1 = Money(1.10, "USD")
        m2 = Money(2.20, "USD")
        total = m1 + m2
        assert total.amount == 3.30, (
            f"$1.10 + $2.20 should be exactly $3.30, got {total.amount!r}"
        )


class TestAccumulatedBalance:
    """Accumulated transactions must not drift."""

    @pytest.mark.fail_to_pass
    def test_accumulated_transactions_balance(self):
        """Adding $0.10 one hundred times must equal exactly $10.00."""
        ledger = Ledger("precision_test")
        for i in range(100):
            ledger.add_transaction(f"small_{i}", Money(0.10, "USD"))

        balance = ledger.get_balance()
        # With float: 0.1 added 100 times ≈ 9.99999999999998 (not 10.0)
        assert balance.amount == 10.00, (
            f"100 × $0.10 should equal $10.00, got {balance.amount!r}"
        )


class TestMonthlyBatchTotals:
    """Monthly batch report totals must be exact."""

    @pytest.mark.fail_to_pass
    def test_monthly_batch_report_totals(self):
        """Tax on many transactions must total correctly."""
        calc = TaxCalculator(rate=0.1)
        ledger = Ledger("monthly_batch")

        now = datetime(2025, 3, 15, tzinfo=timezone.utc)
        for i in range(50):
            txn = ledger.add_transaction(
                f"sale_{i}", Money(19.99, "USD"), category="sales"
            )
            txn.timestamp = now

        tax_ledger = calc.apply_tax_to_ledger(ledger, category="sales")
        total_tax = tax_ledger.get_balance()

        # 50 × 19.99 × 0.1 = 99.95 exactly
        # With float this drifts to something like 99.95000000000006
        assert total_tax.amount == 99.95, (
            f"Total tax should be exactly $99.95, got {total_tax.amount!r}"
        )

        # Also check that the original ledger balance is exact
        sales_total = ledger.get_balance()
        assert sales_total.amount == 999.50, (
            f"Sales total should be $999.50, got {sales_total.amount!r}"
        )
