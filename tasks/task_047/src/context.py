"""Context for template variable storage and retrieval."""


class Context:
    """Stores variables for template rendering.

    Supports nested access via dot notation (e.g., 'user.name').
    """

    def __init__(self, data: dict = None):
        """Initialize context with optional data dictionary.

        Args:
            data: Initial variables. Can contain nested dicts.
        """
        self._data = dict(data) if data else {}

    def get(self, key: str, default=None):
        """Get a value by key, supporting dot notation.

        Args:
            key: Variable name, optionally with dots for nesting.
                 E.g., 'user.name' looks up data['user']['name'].
            default: Value to return if key not found.

        Returns:
            The value, or default if not found.
        """
        parts = key.split(".")
        current = self._data
        for part in parts:
            if isinstance(current, dict):
                if part not in current:
                    return default
                current = current[part]
            elif hasattr(current, part):
                current = getattr(current, part)
            else:
                return default
        return current

    def set(self, key: str, value) -> None:
        """Set a value by key. Does not support dot notation for setting.

        Args:
            key: Variable name (simple, no dots).
            value: The value to store.
        """
        self._data[key] = value

    def has(self, key: str) -> bool:
        """Check if a key exists (supports dot notation)."""
        return self.get(key, _SENTINEL) is not _SENTINEL

    def child(self, **extra) -> "Context":
        """Create a child context with additional variables.

        The child shares the parent data but can override values.
        """
        merged = dict(self._data)
        merged.update(extra)
        return Context(merged)

    @property
    def data(self) -> dict:
        """Return a copy of the underlying data."""
        return dict(self._data)


_SENTINEL = object()
