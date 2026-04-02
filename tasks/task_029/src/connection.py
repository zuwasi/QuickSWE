"""Connection managing transaction lifecycle."""

from .storage import Storage
from .journal import Journal
from .transaction import Transaction


class Connection:
    """Database connection that manages transactions.

    Provides a high-level API for working with transactions and
    the underlying storage.
    """

    def __init__(self, storage=None):
        self._storage = storage or Storage()
        self._journal = Journal()
        self._current_transaction = None
        self._transaction_count = 0
        self._auto_commit = False

    @property
    def storage(self):
        return self._storage

    @property
    def journal(self):
        return self._journal

    @property
    def in_transaction(self):
        return self._current_transaction is not None and self._current_transaction.is_active

    @property
    def current_transaction(self):
        return self._current_transaction

    def begin(self):
        """Begin a new transaction."""
        if self.in_transaction:
            raise RuntimeError("Transaction already in progress")

        txn = Transaction(self._storage, self._journal)
        txn.begin()
        self._current_transaction = txn
        self._transaction_count += 1
        return txn

    def commit(self):
        """Commit the current transaction."""
        if not self.in_transaction:
            raise RuntimeError("No transaction in progress")
        self._current_transaction.commit()

    def rollback(self):
        """Roll back the current transaction."""
        if not self.in_transaction:
            raise RuntimeError("No transaction in progress")
        self._current_transaction.rollback()

    def savepoint(self, name):
        """Create a savepoint in the current transaction."""
        if not self.in_transaction:
            raise RuntimeError("No transaction in progress")
        self._current_transaction.savepoint(name)

    def rollback_to_savepoint(self, name):
        """Roll back to a savepoint."""
        if not self.in_transaction:
            raise RuntimeError("No transaction in progress")
        self._current_transaction.rollback_to_savepoint(name)

    def release_savepoint(self, name):
        """Release a savepoint."""
        if not self.in_transaction:
            raise RuntimeError("No transaction in progress")
        self._current_transaction.release_savepoint(name)

    def set(self, key, value):
        """Set a value (auto-commits if not in transaction)."""
        if self.in_transaction:
            self._current_transaction.set(key, value)
        elif self._auto_commit:
            self._storage.set(key, value)
        else:
            raise RuntimeError("No transaction and auto_commit is off")

    def get(self, key, default=None):
        """Get a value."""
        return self._storage.get(key, default)

    def delete(self, key):
        """Delete a value."""
        if self.in_transaction:
            self._current_transaction.delete(key)
        elif self._auto_commit:
            self._storage.delete(key)
        else:
            raise RuntimeError("No transaction and auto_commit is off")

    def get_all(self):
        """Get all data."""
        return self._storage.get_all()

    def enable_auto_commit(self):
        """Enable auto-commit mode."""
        self._auto_commit = True

    def disable_auto_commit(self):
        """Disable auto-commit mode."""
        self._auto_commit = False

    def get_stats(self):
        """Return connection statistics."""
        return {
            'transaction_count': self._transaction_count,
            'journal_size': self._journal.size,
            'storage_size': self._storage.size(),
            'in_transaction': self.in_transaction,
            'auto_commit': self._auto_commit,
        }

    def __repr__(self):
        return (
            f"Connection(in_txn={self.in_transaction}, "
            f"txn_count={self._transaction_count})"
        )
