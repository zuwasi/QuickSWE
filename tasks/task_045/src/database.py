"""Mock database for ETL pipeline."""


class MockDatabase:
    """Simple in-memory database mock for testing ETL pipelines."""

    def __init__(self):
        self._tables: dict[str, list[dict]] = {}
        self._insert_count = 0

    def create_table(self, name: str) -> None:
        """Create a table if it doesn't exist."""
        if name not in self._tables:
            self._tables[name] = []

    def insert(self, table: str, record: dict) -> int:
        """Insert a record into a table. Returns the row ID."""
        if table not in self._tables:
            self._tables[table] = []
        self._insert_count += 1
        record = dict(record)
        record["_id"] = self._insert_count
        self._tables[table].append(record)
        return self._insert_count

    def insert_many(self, table: str, records: list[dict]) -> list[int]:
        """Insert multiple records. Returns list of row IDs."""
        ids = []
        for rec in records:
            ids.append(self.insert(table, rec))
        return ids

    def query(self, table: str, **filters) -> list[dict]:
        """Query records from a table with optional field filters."""
        if table not in self._tables:
            return []
        results = self._tables[table]
        for key, value in filters.items():
            results = [r for r in results if r.get(key) == value]
        return results

    def count(self, table: str) -> int:
        """Return the number of records in a table."""
        return len(self._tables.get(table, []))

    def all_records(self, table: str) -> list[dict]:
        """Return all records in a table."""
        return list(self._tables.get(table, []))

    def clear(self, table: str) -> None:
        """Clear all records from a table."""
        self._tables[table] = []

    @property
    def total_inserts(self) -> int:
        return self._insert_count
