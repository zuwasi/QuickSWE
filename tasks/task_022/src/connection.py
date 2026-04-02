"""Mock database connection for testing."""


class MockConnection:
    """Simulates a database connection that records executed queries."""

    def __init__(self):
        self._history = []

    def execute(self, query_builder) -> str:
        """Execute a query builder — stores the SQL and returns it."""
        sql = query_builder.build()
        self._history.append(sql)
        return sql

    @property
    def history(self):
        """Return list of all executed SQL strings."""
        return list(self._history)

    @property
    def last_query(self):
        """Return the most recently executed query."""
        if not self._history:
            return None
        return self._history[-1]

    def clear(self):
        """Clear query history."""
        self._history.clear()

    def __len__(self):
        return len(self._history)
