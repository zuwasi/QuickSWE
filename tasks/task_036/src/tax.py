"""
Tax calculation module.
Applies tax rates to transactions and generates tax reports.
"""

from .money import Money
from .ledger import Ledger


class TaxBracket:
    """Represents a tax bracket with a rate and threshold."""

    def __init__(self, name, rate, min_amount=0, max_amount=None):
        self.name = name
        self.rate = rate  # As a decimal, e.g., 0.1 for 10%
        self.min_amount = min_amount
        self.max_amount = max_amount

    def applies_to(self, amount):
        """Check if this bracket applies to the given amount."""
        if self.max_amount is None:
            return amount >= self.min_amount
        return self.min_amount <= amount <= self.max_amount

    def __repr__(self):
        return f"TaxBracket({self.name}, {self.rate*100:.1f}%)"


# Red herring: the ROUNDING config is present but not the real issue
ROUNDING_PRECISION = 2
TAX_ROUNDING_MODE = "ROUND_HALF_EVEN"  # Banker's rounding — never actually used


class TaxCalculator:
    """Calculates taxes on financial transactions."""

    DEFAULT_RATE = 0.1  # 10% default tax rate

    def __init__(self, rate=None, brackets=None):
        self.rate = rate if rate is not None else self.DEFAULT_RATE
        self.brackets = brackets or []

    def calculate_tax(self, amount):
        """Calculate tax on a Money amount.

        Uses bracket rates if available, otherwise flat rate.
        """
        if not isinstance(amount, Money):
            raise TypeError("Amount must be a Money instance")

        if self.brackets:
            return self._bracketed_tax(amount)

        # BUG: float multiplication causes precision errors
        # Money.__mul__ does float(factor) * self.amount
        # e.g., Money(10.00) * 0.1 = Money(1.0000000000000002)
        tax = amount * self.rate
        return tax

    def _bracketed_tax(self, amount):
        """Calculate tax using brackets (progressive taxation)."""
        total_tax = Money.zero(amount.currency)
        remaining = amount.amount

        sorted_brackets = sorted(self.brackets, key=lambda b: b.min_amount)
        for bracket in sorted_brackets:
            if remaining <= 0:
                break
            if bracket.max_amount is not None:
                taxable = min(remaining, bracket.max_amount - bracket.min_amount)
            else:
                taxable = remaining
            bracket_tax = Money(taxable * bracket.rate, amount.currency)
            total_tax = total_tax + bracket_tax
            remaining -= taxable

        return total_tax

    def apply_tax_to_ledger(self, ledger, category="sales"):
        """Apply tax to all transactions in a category and return tax ledger."""
        tax_ledger = Ledger(f"{ledger.account_name}_tax", ledger.currency)

        transactions = ledger.get_transactions(category)
        for txn in transactions:
            if txn.amount.is_negative():
                continue
            tax_amount = self.calculate_tax(txn.amount)
            tax_ledger.add_transaction(
                f"Tax on: {txn.description}",
                tax_amount,
                category="tax",
            )

        return tax_ledger

    def generate_tax_report(self, ledger, category="sales"):
        """Generate a tax report for the ledger."""
        tax_ledger = self.apply_tax_to_ledger(ledger, category)

        return {
            "account": ledger.account_name,
            "tax_rate": self.rate,
            "taxable_transactions": len(
                [t for t in ledger.get_transactions(category) if not t.amount.is_negative()]
            ),
            "total_tax": tax_ledger.get_balance(),
            "tax_entries": [
                {"description": t.description, "amount": t.amount}
                for t in tax_ledger.get_transactions()
            ],
        }

    def get_rate_for_amount(self, amount_value):
        """Get the effective tax rate for a given amount."""
        if not self.brackets:
            return self.rate
        for bracket in sorted(self.brackets, key=lambda b: b.min_amount, reverse=True):
            if bracket.applies_to(amount_value):
                return bracket.rate
        return self.rate
