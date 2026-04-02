"""Observable value — wraps a value with change notification callbacks."""


class ObservableValue:
    """A value container that notifies subscribers when the value changes.

    Attributes:
        _value: The wrapped value.
        _subscribers: List of callbacks invoked on change.
        _name: Optional name for debugging.
    """

    def __init__(self, initial_value=None, name=None):
        self._value = initial_value
        self._subscribers = []
        self._name = name or f"ObservableValue@{id(self)}"

    @property
    def name(self):
        return self._name

    def get(self):
        """Return the current value.

        NOTE: This method should participate in automatic dependency tracking
        if a tracking scope is active, but that integration is NOT yet implemented.
        """
        return self._value

    def set(self, new_value):
        """Set a new value. If it differs from the current value, notify subscribers."""
        if new_value == self._value:
            return
        old = self._value
        self._value = new_value
        for callback in self._subscribers[:]:
            callback(old, new_value)

    def subscribe(self, callback):
        """Register a callback(old_value, new_value) to be called on change."""
        self._subscribers.append(callback)
        return lambda: self._subscribers.remove(callback)

    def __repr__(self):
        return f"ObservableValue({self._value!r}, name={self._name!r})"
