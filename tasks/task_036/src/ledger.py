"""
Ledger for tracking financial transactions.
Maintains a list of debits and credits.
"""

from datetime import datetime, timezone
from .money import Money


class Transaction:
    """A single financial transaction."""

    def __init__(self, description, amount, category="general", timestamp=None):
        if not isinstance(amount, Money):
            raise TypeError("Transaction amount must be a Money instance")
        self.description = description
        self.amount = amount
        self.category = category
        self.timestamp = timestamp or datetime.now(timezone.utc)
        self._posted = False

    def post(self):
        """Mark transaction as posted."""
        self._posted = True

    @property
    def is_posted(self):
        return self._posted

    def __repr__(self):
        status = "posted" if self._posted else "pending"
        return f"Transaction({self.description!r}, {self.amount}, {status})"


class Ledger:
    """Tracks all transactions for an account."""

    def __init__(self, account_name, currency="USD"):
        self.account_name = account_name
        self.currency = currency
        self._transactions = []
        self._reconciled = False  # Red herring flag

    def add_transaction(self, description, amount, category="general"):
        """Add a transaction to the ledger."""
        if isinstance(amount, (int, float)):
            amount = Money(amount, self.currency)
        txn = Transaction(description, amount, category)
        self._transactions.append(txn)
        self._reconciled = False
        return txn

    def get_balance(self):
        """Calculate current balance by summing all transactions."""
        balance = Money.zero(self.currency)
        for txn in self._transactions:
            balance = balance + txn.amount
        return balance

    def get_transactions(self, category=None):
        """Get transactions, optionally filtered by category."""
        if category is None:
            return list(self._transactions)
        return [t for t in self._transactions if t.category == category]

    def get_monthly_summary(self, year, month):
        """Get summary of transactions for a given month."""
        monthly = [
            t for t in self._transactions
            if t.timestamp.year == year and t.timestamp.month == month
        ]

        total_credits = Money.zero(self.currency)
        total_debits = Money.zero(self.currency)

        for txn in monthly:
            if txn.amount.is_negative():
                total_debits = total_debits + txn.amount
            else:
                total_credits = total_credits + txn.amount

        return {
            "period": f"{year}-{month:02d}",
            "transaction_count": len(monthly),
            "total_credits": total_credits,
            "total_debits": total_debits,
            "net": total_credits + total_debits,
        }

    def reconcile(self):
        """Mark all transactions as posted and set reconciled flag."""
        for txn in self._transactions:
            txn.post()
        self._reconciled = True

    def post_all(self):
        """Post all pending transactions."""
        for txn in self._transactions:
            if not txn.is_posted:
                txn.post()

    @property
    def transaction_count(self):
        return len(self._transactions)
