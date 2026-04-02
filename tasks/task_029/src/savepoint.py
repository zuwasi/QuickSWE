"""Savepoint support for nested transactions."""


class Savepoint:
    """Represents a savepoint within a transaction.

    A savepoint marks a point within a transaction that can be rolled
    back to without rolling back the entire transaction.
    """

    def __init__(self, name, transaction_id, journal_position):
        self._name = name
        self._transaction_id = transaction_id
        self._journal_position = journal_position
        self._released = False
        self._rolled_back = False
        self._keys_modified = []

    @property
    def name(self):
        return self._name

    @property
    def transaction_id(self):
        return self._transaction_id

    @property
    def journal_position(self):
        return self._journal_position

    @property
    def is_active(self):
        return not self._released and not self._rolled_back

    @property
    def is_released(self):
        return self._released

    @property
    def is_rolled_back(self):
        return self._rolled_back

    def record_key(self, key):
        """Record that a key was modified within this savepoint."""
        if key not in self._keys_modified:
            self._keys_modified.append(key)

    @property
    def modified_keys(self):
        return list(self._keys_modified)

    def release(self):
        """Release the savepoint (make changes permanent within the transaction)."""
        if not self.is_active:
            raise RuntimeError(f"Savepoint '{self._name}' is not active")
        self._released = True

    def mark_rolled_back(self):
        """Mark this savepoint as rolled back."""
        if not self.is_active:
            raise RuntimeError(f"Savepoint '{self._name}' is not active")
        self._rolled_back = True

    def __repr__(self):
        status = 'active' if self.is_active else ('released' if self._released else 'rolled_back')
        return (
            f"Savepoint(name='{self._name}', txn='{self._transaction_id}', "
            f"pos={self._journal_position}, status={status})"
        )


class SavepointManager:
    """Manages savepoints within a transaction."""

    def __init__(self):
        self._savepoints = {}
        self._stack = []  # Stack for nested savepoints

    def create(self, name, transaction_id, journal_position):
        """Create a new savepoint."""
        if name in self._savepoints:
            raise ValueError(f"Savepoint '{name}' already exists")

        sp = Savepoint(name, transaction_id, journal_position)
        self._savepoints[name] = sp
        self._stack.append(sp)
        return sp

    def get(self, name):
        """Get a savepoint by name."""
        return self._savepoints.get(name)

    def release(self, name):
        """Release a savepoint."""
        sp = self._savepoints.get(name)
        if sp is None:
            raise ValueError(f"Savepoint '{name}' not found")
        sp.release()
        # Remove from stack
        self._stack = [s for s in self._stack if s.name != name]

    def rollback(self, name):
        """Mark a savepoint as rolled back."""
        sp = self._savepoints.get(name)
        if sp is None:
            raise ValueError(f"Savepoint '{name}' not found")
        sp.mark_rolled_back()
        # Remove from stack
        self._stack = [s for s in self._stack if s.name != name]

    @property
    def active_savepoints(self):
        """Return list of active savepoints."""
        return [sp for sp in self._stack if sp.is_active]

    @property
    def current_savepoint(self):
        """Return the most recent active savepoint."""
        for sp in reversed(self._stack):
            if sp.is_active:
                return sp
        return None

    def clear(self):
        """Clear all savepoints."""
        self._savepoints.clear()
        self._stack.clear()

    def __repr__(self):
        active = len(self.active_savepoints)
        return f"SavepointManager(total={len(self._savepoints)}, active={active})"
