"""In-memory storage backend."""

from typing import Any


class InMemoryStorage:
    """Simple dict-based storage backend.

    Tracks access counts for testing purposes.
    """

    def __init__(self):
        self._data: dict[str, dict] = {}
        self._read_count = 0
        self._write_count = 0

    def get(self, key: str) -> dict | None:
        """Retrieve a record by key."""
        self._read_count += 1
        return self._data.get(key)

    def put(self, key: str, value: dict) -> None:
        """Store or update a record."""
        self._write_count += 1
        self._data[key] = dict(value)

    def delete(self, key: str) -> bool:
        """Delete a record by key. Returns True if existed."""
        self._write_count += 1
        if key in self._data:
            del self._data[key]
            return True
        return False

    def all(self) -> list[dict]:
        """Return all records."""
        self._read_count += 1
        return list(self._data.values())

    def count(self) -> int:
        """Return number of stored records."""
        return len(self._data)

    @property
    def read_count(self) -> int:
        """Total number of read operations."""
        return self._read_count

    @property
    def write_count(self) -> int:
        """Total number of write operations."""
        return self._write_count

    def reset_counters(self) -> None:
        """Reset access counters."""
        self._read_count = 0
        self._write_count = 0
