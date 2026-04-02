"""Table — stores rows as a list of dicts with a global registry."""


class Table:
    """In-memory table storing rows as list of dicts.

    Each row is a dict mapping column names to values.
    Tables are registered globally by name for query resolution.
    """

    _registry = {}

    def __init__(self, name, columns=None):
        """Create a table.

        Args:
            name: Table name (used in queries).
            columns: Optional list of column names for validation.
        """
        self._name = name
        self._columns = columns or []
        self._rows = []
        Table._registry[name] = self

    @property
    def name(self):
        return self._name

    @property
    def columns(self):
        if self._columns:
            return list(self._columns)
        if self._rows:
            return list(self._rows[0].keys())
        return []

    def add_row(self, row):
        """Add a row (dict) to the table.

        Args:
            row: Dict mapping column names to values.

        Raises:
            ValueError: If columns were specified and row has wrong keys.
        """
        if self._columns:
            missing = set(self._columns) - set(row.keys())
            if missing:
                raise ValueError(f"Missing columns: {missing}")
        self._rows.append(dict(row))

    def get_rows(self):
        """Return a copy of all rows."""
        return [dict(r) for r in self._rows]

    def __len__(self):
        return len(self._rows)

    @classmethod
    def get_table(cls, name):
        """Look up a registered table by name.

        Raises:
            KeyError: If table not found.
        """
        if name not in cls._registry:
            raise KeyError(f"Table '{name}' not found")
        return cls._registry[name]

    @classmethod
    def clear_registry(cls):
        """Remove all registered tables."""
        cls._registry.clear()

    def __repr__(self):
        return f"Table({self._name!r}, rows={len(self._rows)})"
