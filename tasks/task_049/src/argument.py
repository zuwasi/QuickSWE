"""Argument definitions for CLI parser."""

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Argument:
    """Represents a single CLI argument.

    Attributes:
        name: The argument name (without -- prefix for optional).
        short: Short flag name (e.g., '-v'). None for positional.
        arg_type: Type to coerce the value to (str, int, float, bool).
        required: Whether the argument must be provided.
        default: Default value if not provided.
        is_flag: If True, this is a boolean flag (no value consumed).
        is_positional: If True, this is a positional argument.
        help: Help text description.
    """
    name: str
    short: str | None = None
    arg_type: type = str
    required: bool = False
    default: Any = None
    is_flag: bool = False
    is_positional: bool = False
    help: str = ""

    @property
    def long_flag(self) -> str:
        """Return the --name form."""
        return f"--{self.name}"

    @property
    def display_name(self) -> str:
        """Human-readable name for error messages and help."""
        if self.is_positional:
            return self.name
        parts = []
        if self.short:
            parts.append(self.short)
        parts.append(self.long_flag)
        return ", ".join(parts)


class Namespace:
    """Container for parsed argument values with attribute access.

    Example:
        ns = Namespace(name="Alice", verbose=True)
        assert ns.name == "Alice"
        assert ns.verbose is True
    """

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self):
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"Namespace({attrs})"

    def __eq__(self, other):
        if not isinstance(other, Namespace):
            return NotImplemented
        return self.__dict__ == other.__dict__

    def to_dict(self) -> dict:
        return dict(self.__dict__)


class ParseError(Exception):
    """Raised when argument parsing fails."""
    pass
