"""Computed value — derives its value from a function over observables.

TODO: Implement ComputedValue so that:
1. It evaluates lazily (only on .get() when dirty).
2. Dependencies are tracked automatically via the Scope system.
3. Diamond dependencies don't cause redundant recomputations.
4. If the compute function raises, the error is stored and re-raised on .get().
"""


class ComputedValue:
    """A value derived from a computation over ObservableValues.

    Args:
        compute_fn: A callable that returns the computed value.
                    During its execution, any ObservableValue.get() calls
                    should be automatically captured as dependencies.
        name: Optional name for debugging.
    """

    def __init__(self, compute_fn, name=None):
        self._compute_fn = compute_fn
        self._name = name or f"ComputedValue@{id(self)}"
        # TODO: Implement the rest

    @property
    def name(self):
        return self._name

    def get(self):
        """Return the computed value, recomputing if dirty."""
        # TODO: Implement lazy evaluation with automatic dependency tracking
        raise NotImplementedError("ComputedValue.get() is not yet implemented")

    def __repr__(self):
        return f"ComputedValue(name={self._name!r})"
