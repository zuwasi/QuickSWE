"""In-memory key-value storage."""


class Storage:
    """Simple in-memory key-value store.

    Supports basic CRUD operations and snapshots for transaction support.
    """

    def __init__(self):
        self._data = {}
        self._snapshots = []

    def get(self, key, default=None):
        """Get a value by key."""
        return self._data.get(key, default)

    def set(self, key, value):
        """Set a key-value pair."""
        self._data[key] = value

    def delete(self, key):
        """Delete a key."""
        if key in self._data:
            del self._data[key]
            return True
        return False

    def exists(self, key):
        """Check if a key exists."""
        return key in self._data

    def keys(self):
        """Return all keys."""
        return list(self._data.keys())

    def values(self):
        """Return all values."""
        return list(self._data.values())

    def items(self):
        """Return all key-value pairs."""
        return list(self._data.items())

    def size(self):
        """Return number of stored items."""
        return len(self._data)

    def clear(self):
        """Clear all data."""
        self._data.clear()

    def snapshot(self):
        """Create a snapshot of current state."""
        self._snapshots.append(dict(self._data))

    def restore_snapshot(self):
        """Restore the most recent snapshot."""
        if self._snapshots:
            self._data = self._snapshots.pop()
        else:
            raise RuntimeError("No snapshot to restore")

    def discard_snapshot(self):
        """Discard the most recent snapshot without restoring."""
        if self._snapshots:
            self._snapshots.pop()

    def get_all(self):
        """Return a copy of all data."""
        return dict(self._data)

    def bulk_set(self, items):
        """Set multiple key-value pairs."""
        self._data.update(items)

    def bulk_delete(self, keys):
        """Delete multiple keys."""
        for key in keys:
            self._data.pop(key, None)

    def __repr__(self):
        return f"Storage({self._data})"
