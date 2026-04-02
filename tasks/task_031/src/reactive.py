"""Top-level API for the reactive system.

Convenience functions that wrap the underlying classes.
These functions should work once the underlying classes are implemented.
"""

from .observable_value import ObservableValue
from .computed import ComputedValue
from .binding import Binding
from .scope import Scope


def reactive(initial_value=None, name=None):
    """Create a new ObservableValue."""
    return ObservableValue(initial_value, name=name)


def computed(fn, name=None):
    """Create a new ComputedValue from a function."""
    return ComputedValue(fn, name=name)


def bind(source, target, transform=None, reverse_transform=None):
    """Create a two-way binding between two ObservableValues."""
    return Binding(source, target, transform=transform, reverse_transform=reverse_transform)


def batch():
    """Return a batch context manager."""
    return Scope.batch()
