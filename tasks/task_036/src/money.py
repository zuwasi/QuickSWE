"""
Money representation for financial calculations.
Handles currency amounts and arithmetic operations.
"""


class Money:
    """Represents a monetary amount with currency."""

    VALID_CURRENCIES = {"USD", "EUR", "GBP", "JPY", "CAD"}
    ROUNDING_MODE = "HALF_UP"  # Red herring — not actually used anywhere

    def __init__(self, amount, currency="USD"):
        if currency not in self.VALID_CURRENCIES:
            raise ValueError(f"Unsupported currency: {currency}")
        # BUG: Using float for monetary amounts causes precision errors
        # e.g., 10.00 * 0.1 = 1.0000000000000002 in float
        self.amount = float(amount)
        self.currency = currency

    def __add__(self, other):
        self._check_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other):
        self._check_currency(other)
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, factor):
        """Multiply money by a scalar (e.g., tax rate)."""
        if isinstance(factor, Money):
            raise TypeError("Cannot multiply Money by Money")
        return Money(self.amount * float(factor), self.currency)

    def __rmul__(self, factor):
        return self.__mul__(factor)

    def __eq__(self, other):
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount == other.amount and self.currency == other.currency

    def __repr__(self):
        return f"Money({self.amount:.2f}, '{self.currency}')"

    def __str__(self):
        symbols = {"USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "CAD": "C$"}
        sym = symbols.get(self.currency, self.currency)
        return f"{sym}{self.amount:.2f}"

    def round_to_cents(self):
        """Round to 2 decimal places."""
        # Red herring: this method exists but doesn't fix the core issue
        # because the accumulated error happens BEFORE rounding
        return Money(round(self.amount, 2), self.currency)

    def _check_currency(self, other):
        if not isinstance(other, Money):
            raise TypeError(f"Cannot operate on Money and {type(other)}")
        if self.currency != other.currency:
            raise ValueError(
                f"Currency mismatch: {self.currency} vs {other.currency}"
            )

    def to_dict(self):
        return {"amount": self.amount, "currency": self.currency}

    @classmethod
    def from_dict(cls, data):
        return cls(data["amount"], data["currency"])

    @classmethod
    def zero(cls, currency="USD"):
        return cls(0, currency)

    def is_negative(self):
        return self.amount < 0

    def is_zero(self):
        return self.amount == 0

    def abs(self):
        return Money(abs(self.amount), self.currency)
