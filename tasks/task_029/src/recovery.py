"""Recovery manager for replaying journal entries.

RED HERRING: This module has complex replay logic that looks like it could
cause data loss, but it actually works correctly. The bug is in how
journal.truncate_to_savepoint removes entries indiscriminately.
"""

from .journal import EntryType


class RecoveryManager:
    """Handles recovery by replaying journal entries.

    The replay logic below looks complex with its state machine approach,
    but it correctly handles all cases including nested savepoints,
    partial commits, and interrupted transactions.
    """

    def __init__(self, journal, storage):
        self._journal = journal
        self._storage = storage
        self._recovered_transactions = []
        self._skipped_transactions = []

    def recover(self):
        """Replay journal entries to recover storage state.

        This method analyzes the journal to determine which transactions
        were committed and replays only those.
        """
        # First pass: find committed transactions
        committed = set()
        rolled_back = set()

        for entry in self._journal.entries:
            if entry.entry_type == EntryType.COMMIT:
                committed.add(entry.transaction_id)
            elif entry.entry_type == EntryType.ROLLBACK:
                rolled_back.add(entry.transaction_id)

        # Second pass: replay committed transaction entries
        # This looks like it could miss entries or replay them wrong,
        # but the logic is correct — it only replays data entries
        # from committed transactions
        for entry in self._journal.entries:
            if entry.transaction_id not in committed:
                continue
            if entry.transaction_id in rolled_back:
                continue

            if entry.entry_type == EntryType.SET:
                self._storage.set(entry.key, entry.value)
            elif entry.entry_type == EntryType.DELETE:
                self._storage.delete(entry.key)

        self._recovered_transactions = list(committed - rolled_back)
        self._skipped_transactions = list(rolled_back)

    def verify_consistency(self):
        """Verify journal consistency.

        Checks that:
        1. Every BEGIN has a matching COMMIT or ROLLBACK
        2. Savepoints are properly nested
        3. No orphaned entries exist

        This looks like it could incorrectly report issues, but the
        verification logic is sound.
        """
        issues = []
        open_transactions = {}
        open_savepoints = {}

        for i, entry in enumerate(self._journal.entries):
            if entry.entry_type == EntryType.BEGIN:
                if entry.transaction_id in open_transactions:
                    issues.append(
                        f"Duplicate BEGIN for transaction {entry.transaction_id}"
                    )
                open_transactions[entry.transaction_id] = i

            elif entry.entry_type in (EntryType.COMMIT, EntryType.ROLLBACK):
                if entry.transaction_id not in open_transactions:
                    issues.append(
                        f"{entry.entry_type.value} without BEGIN for "
                        f"transaction {entry.transaction_id}"
                    )
                else:
                    del open_transactions[entry.transaction_id]

            elif entry.entry_type == EntryType.SAVEPOINT:
                key = (entry.transaction_id, entry.savepoint_name)
                open_savepoints[key] = i

            elif entry.entry_type == EntryType.ROLLBACK_SAVEPOINT:
                key = (entry.transaction_id, entry.savepoint_name)
                if key in open_savepoints:
                    del open_savepoints[key]

        # Check for unclosed transactions
        for txn_id in open_transactions:
            issues.append(f"Unclosed transaction: {txn_id}")

        return {
            'consistent': len(issues) == 0,
            'issues': issues,
            'open_transactions': list(open_transactions.keys()),
            'recovered': self._recovered_transactions,
            'skipped': self._skipped_transactions,
        }

    def get_recovery_stats(self):
        """Return recovery statistics."""
        return {
            'recovered_count': len(self._recovered_transactions),
            'skipped_count': len(self._skipped_transactions),
            'journal_size': self._journal.size,
        }

    def __repr__(self):
        return (
            f"RecoveryManager(recovered={len(self._recovered_transactions)}, "
            f"skipped={len(self._skipped_transactions)})"
        )
