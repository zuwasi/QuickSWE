"""Transaction manager with savepoint support."""

import uuid

from .journal import Journal, EntryType
from .savepoint import SavepointManager
from .storage import Storage


class Transaction:
    """Manages a transaction with savepoint support.

    Provides begin/commit/rollback and nested savepoint operations.
    Uses a journal for write-ahead logging and a storage backend.
    """

    def __init__(self, storage, journal):
        self._storage = storage
        self._journal = journal
        self._id = None
        self._active = False
        self._savepoint_mgr = SavepointManager()
        self._committed = False
        self._rolled_back = False

    @property
    def id(self):
        return self._id

    @property
    def is_active(self):
        return self._active

    @property
    def is_committed(self):
        return self._committed

    @property
    def is_rolled_back(self):
        return self._rolled_back

    def begin(self):
        """Begin the transaction."""
        if self._active:
            raise RuntimeError("Transaction already active")
        self._id = str(uuid.uuid4())[:8]
        self._active = True
        self._journal.log_begin(self._id)
        self._storage.snapshot()

    def set(self, key, value):
        """Set a key-value pair within the transaction."""
        if not self._active:
            raise RuntimeError("No active transaction")

        old_value = self._storage.get(key)
        current_sp = self._savepoint_mgr.current_savepoint
        sp_name = current_sp.name if current_sp else None

        self._journal.log_set(
            key, value, old_value,
            transaction_id=self._id,
            savepoint_name=sp_name
        )
        self._storage.set(key, value)

        if current_sp:
            current_sp.record_key(key)

    def delete(self, key):
        """Delete a key within the transaction."""
        if not self._active:
            raise RuntimeError("No active transaction")

        old_value = self._storage.get(key)
        current_sp = self._savepoint_mgr.current_savepoint

        self._journal.log_delete(
            key, old_value,
            transaction_id=self._id,
            savepoint_name=current_sp.name if current_sp else None
        )
        self._storage.delete(key)

        if current_sp:
            current_sp.record_key(key)

    def get(self, key, default=None):
        """Get a value within the transaction."""
        return self._storage.get(key, default)

    def commit(self):
        """Commit the transaction."""
        if not self._active:
            raise RuntimeError("No active transaction")

        self._journal.log_commit(self._id)
        self._storage.discard_snapshot()
        self._active = False
        self._committed = True

    def rollback(self):
        """Roll back the entire transaction."""
        if not self._active:
            raise RuntimeError("No active transaction")

        self._journal.log_rollback(self._id)
        self._storage.restore_snapshot()
        self._active = False
        self._rolled_back = True
        self._savepoint_mgr.clear()

    def savepoint(self, name):
        """Create a savepoint."""
        if not self._active:
            raise RuntimeError("No active transaction")

        journal_pos = self._journal.size
        self._journal.log_savepoint(self._id, name)
        self._savepoint_mgr.create(name, self._id, journal_pos)

    def release_savepoint(self, name):
        """Release a savepoint (make its changes permanent in the transaction)."""
        if not self._active:
            raise RuntimeError("No active transaction")
        self._savepoint_mgr.release(name)

    def rollback_to_savepoint(self, name):
        """Roll back to a savepoint.

        This should undo only the changes made within the savepoint,
        not changes made by the parent transaction after the savepoint.
        """
        if not self._active:
            raise RuntimeError("No active transaction")

        sp = self._savepoint_mgr.get(name)
        if sp is None:
            raise ValueError(f"Savepoint '{name}' not found")

        # Get entries to undo (entries belonging to this savepoint)
        undo_entries = self._journal.get_undo_entries(name)

        # Undo each entry in reverse order
        for entry in undo_entries:
            if entry.entry_type == EntryType.SET:
                if entry.old_value is not None:
                    self._storage.set(entry.key, entry.old_value)
                else:
                    self._storage.delete(entry.key)
            elif entry.entry_type == EntryType.DELETE:
                if entry.old_value is not None:
                    self._storage.set(entry.key, entry.old_value)

        # BUG: truncate_to_savepoint removes ALL entries after the savepoint
        # marker, including parent transaction entries logged after the savepoint.
        # This means if the parent transaction wrote data after creating the
        # savepoint, those journal entries are lost.
        self._journal.truncate_to_savepoint(name)
        self._savepoint_mgr.rollback(name)

    def get_all(self):
        """Get all data in storage."""
        return self._storage.get_all()

    def __repr__(self):
        status = 'active' if self._active else ('committed' if self._committed else 'rolled_back')
        return f"Transaction(id={self._id}, status={status})"
