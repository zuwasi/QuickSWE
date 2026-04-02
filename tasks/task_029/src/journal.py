"""Write-ahead journal for transaction logging."""

import time
from enum import Enum


class EntryType(Enum):
    SET = 'SET'
    DELETE = 'DELETE'
    BEGIN = 'BEGIN'
    COMMIT = 'COMMIT'
    ROLLBACK = 'ROLLBACK'
    SAVEPOINT = 'SAVEPOINT'
    RELEASE_SAVEPOINT = 'RELEASE_SAVEPOINT'
    ROLLBACK_SAVEPOINT = 'ROLLBACK_SAVEPOINT'


class JournalEntry:
    """A single entry in the write-ahead journal."""

    def __init__(self, entry_type, key=None, value=None, old_value=None,
                 transaction_id=None, savepoint_name=None):
        self.entry_type = entry_type
        self.key = key
        self.value = value
        self.old_value = old_value
        self.transaction_id = transaction_id
        self.savepoint_name = savepoint_name
        self.timestamp = time.time()
        self.sequence = None  # Set by journal

    def is_data_entry(self):
        """Check if this is a data modification entry."""
        return self.entry_type in (EntryType.SET, EntryType.DELETE)

    def __repr__(self):
        if self.is_data_entry():
            return (
                f"JournalEntry({self.entry_type.value}, key={self.key!r}, "
                f"txn={self.transaction_id}, sp={self.savepoint_name})"
            )
        return (
            f"JournalEntry({self.entry_type.value}, "
            f"txn={self.transaction_id}, sp={self.savepoint_name})"
        )


class Journal:
    """Write-ahead journal that logs all data modifications.

    Used for transaction support — entries can be replayed or rolled back.
    Each entry includes the transaction ID and optional savepoint name.
    """

    def __init__(self):
        self._entries = []
        self._sequence = 0
        self._checkpoints = []

    @property
    def entries(self):
        return list(self._entries)

    @property
    def size(self):
        return len(self._entries)

    def append(self, entry):
        """Append an entry to the journal."""
        entry.sequence = self._sequence
        self._sequence += 1
        self._entries.append(entry)

    def log_set(self, key, value, old_value=None, transaction_id=None, savepoint_name=None):
        """Log a SET operation."""
        entry = JournalEntry(
            EntryType.SET,
            key=key,
            value=value,
            old_value=old_value,
            transaction_id=transaction_id,
            savepoint_name=savepoint_name,
        )
        self.append(entry)
        return entry

    def log_delete(self, key, old_value=None, transaction_id=None, savepoint_name=None):
        """Log a DELETE operation."""
        entry = JournalEntry(
            EntryType.DELETE,
            key=key,
            old_value=old_value,
            transaction_id=transaction_id,
            savepoint_name=savepoint_name,
        )
        self.append(entry)
        return entry

    def log_begin(self, transaction_id):
        """Log transaction begin."""
        entry = JournalEntry(EntryType.BEGIN, transaction_id=transaction_id)
        self.append(entry)

    def log_commit(self, transaction_id):
        """Log transaction commit."""
        entry = JournalEntry(EntryType.COMMIT, transaction_id=transaction_id)
        self.append(entry)

    def log_rollback(self, transaction_id):
        """Log transaction rollback."""
        entry = JournalEntry(EntryType.ROLLBACK, transaction_id=transaction_id)
        self.append(entry)

    def log_savepoint(self, transaction_id, savepoint_name):
        """Log savepoint creation."""
        entry = JournalEntry(
            EntryType.SAVEPOINT,
            transaction_id=transaction_id,
            savepoint_name=savepoint_name,
        )
        self.append(entry)

    def get_entries_for_transaction(self, transaction_id):
        """Get all entries for a specific transaction."""
        return [e for e in self._entries if e.transaction_id == transaction_id]

    def get_entries_for_savepoint(self, savepoint_name):
        """Get data entries that belong to a specific savepoint."""
        return [
            e for e in self._entries
            if e.savepoint_name == savepoint_name and e.is_data_entry()
        ]

    def find_savepoint_index(self, savepoint_name):
        """Find the index of the savepoint marker in the journal."""
        for i, entry in enumerate(self._entries):
            if (entry.entry_type == EntryType.SAVEPOINT and
                    entry.savepoint_name == savepoint_name):
                return i
        return -1

    def truncate_to_savepoint(self, savepoint_name):
        """Remove entries belonging to a savepoint from the journal.

        BUG: This method truncates ALL entries from the savepoint marker
        onward, regardless of which savepoint/transaction they belong to.
        It should only remove entries where entry.savepoint_name matches
        the given savepoint_name, preserving parent transaction entries
        and the entries from other savepoints that happen to be interleaved.

        The correct implementation would be:
            self._entries = [
                e for e in self._entries
                if not (e.savepoint_name == savepoint_name) and
                   e.entry_type != EntryType.SAVEPOINT or
                   e.savepoint_name != savepoint_name
            ]
        Or more clearly: remove entries tagged with this savepoint and
        the savepoint marker itself, but keep everything else.
        """
        index = self.find_savepoint_index(savepoint_name)
        if index < 0:
            raise ValueError(f"Savepoint '{savepoint_name}' not found in journal")

        # BUG: Truncates everything from the savepoint marker onward
        self._entries = self._entries[:index]

    def get_undo_entries(self, savepoint_name):
        """Get entries that need to be undone for a savepoint rollback.

        Returns entries in reverse order (most recent first).
        """
        entries = self.get_entries_for_savepoint(savepoint_name)
        return list(reversed(entries))

    def checkpoint(self):
        """Create a checkpoint at the current position."""
        self._checkpoints.append(len(self._entries))

    def entries_since_checkpoint(self):
        """Get entries since the last checkpoint."""
        if not self._checkpoints:
            return list(self._entries)
        pos = self._checkpoints[-1]
        return list(self._entries[pos:])

    def clear(self):
        """Clear the entire journal."""
        self._entries.clear()
        self._sequence = 0
        self._checkpoints.clear()

    def __len__(self):
        return len(self._entries)

    def __repr__(self):
        return f"Journal(entries={len(self._entries)}, seq={self._sequence})"
