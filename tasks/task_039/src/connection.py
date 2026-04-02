"""
Database connection abstraction.
Simulates a database connection with execute, commit, and rollback.
"""

import time


class ConnectionError(Exception):
    """Raised when a connection operation fails."""
    pass


class Connection:
    """Simulates a database connection.

    In production this would wrap a real DB driver. Here we simulate
    with in-memory state for testing.
    """

    _id_counter = 0

    def __init__(self, host="localhost", port=5432):
        Connection._id_counter += 1
        self.id = Connection._id_counter
        self.host = host
        self.port = port
        self._connected = True
        self._in_transaction = False
        self._operations = []
        self._fail_on_rollback = False  # Test hook
        self._fail_on_commit = False    # Test hook
        self._created_at = time.monotonic()

    def execute(self, query, params=None):
        """Execute a query on this connection."""
        if not self._connected:
            raise ConnectionError(f"Connection {self.id} is closed")
        self._operations.append(("execute", query, params))
        return {"status": "ok", "connection_id": self.id}

    def commit(self):
        """Commit the current transaction."""
        if not self._connected:
            raise ConnectionError(f"Connection {self.id} is closed")
        if self._fail_on_commit:
            raise ConnectionError(
                f"Connection {self.id}: commit failed (simulated)"
            )
        self._in_transaction = False
        self._operations.append(("commit",))

    def rollback(self):
        """Rollback the current transaction.

        NOTE: This can raise if the connection is in a bad state.
        This is the root cause of the pool leak — when rollback raises
        inside Transaction.__exit__, the connection is never returned.
        """
        if not self._connected:
            raise ConnectionError(f"Connection {self.id} is closed")
        if self._fail_on_rollback:
            raise ConnectionError(
                f"Connection {self.id}: rollback failed (simulated)"
            )
        self._in_transaction = False
        self._operations.append(("rollback",))

    def begin(self):
        """Begin a new transaction."""
        if not self._connected:
            raise ConnectionError(f"Connection {self.id} is closed")
        self._in_transaction = True
        self._operations.append(("begin",))

    def close(self):
        """Close the connection."""
        self._connected = False

    def reset(self):
        """Reset connection state for reuse in pool."""
        if self._in_transaction:
            self.rollback()
        self._operations = []

    @property
    def is_connected(self):
        return self._connected

    @property
    def is_idle(self):
        return self._connected and not self._in_transaction

    @property
    def age(self):
        return time.monotonic() - self._created_at

    def __repr__(self):
        status = "connected" if self._connected else "closed"
        txn = ", in_txn" if self._in_transaction else ""
        return f"Connection(id={self.id}, {status}{txn})"
