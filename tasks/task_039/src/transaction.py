"""
Transaction context manager.
Wraps connection operations in a transaction with commit/rollback.
"""

from .connection import ConnectionError as ConnError


class TransactionError(Exception):
    """Raised when a transaction operation fails."""
    pass


class Transaction:
    """Context manager for database transactions.

    Usage:
        conn = pool.acquire()
        with Transaction(conn, pool) as txn:
            txn.execute("INSERT INTO ...")
            txn.execute("UPDATE ...")
        # auto-commits on success, rolls back on exception
    """

    def __init__(self, connection, pool):
        self._connection = connection
        self._pool = pool
        self._completed = False

    def __enter__(self):
        self._connection.begin()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Handle transaction completion.

        BUG: When an exception occurred (exc_type is not None), we try
        to rollback. But if rollback() itself raises (e.g., connection
        is in a bad state), the ORIGINAL exception is lost AND the
        connection is never returned to the pool — causing a leak.
        """
        try:
            if exc_type is None:
                # Happy path: commit and release
                self._connection.commit()
            else:
                # Error path: rollback
                # BUG: if rollback raises, we skip the finally-release
                # because there IS no finally here — release is below
                self._connection.rollback()
        except ConnError as e:
            # BUG: we catch the rollback/commit error but still don't
            # release the connection to the pool!
            raise TransactionError(
                f"Transaction cleanup failed: {e}"
            ) from exc_val

        # BUG: This line is only reached if no exception occurs above.
        # If rollback raises, we never get here, and the connection
        # is leaked from the pool.
        self._pool.release(self._connection)
        self._completed = True

        return False  # Don't suppress the original exception

    def execute(self, query, params=None):
        """Execute a query within this transaction."""
        if self._completed:
            raise TransactionError("Transaction already completed")
        return self._connection.execute(query, params)

    @property
    def connection_id(self):
        return self._connection.id

    def __repr__(self):
        status = "completed" if self._completed else "active"
        return f"Transaction(conn={self._connection.id}, {status})"
