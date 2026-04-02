"""
Connection pool for managing database connections.
Provides acquire/release semantics with a fixed pool size.
"""

import threading
import time
from .connection import Connection


class PoolExhaustedError(Exception):
    """Raised when the pool has no available connections."""
    pass


class ConnectionPool:
    """A fixed-size pool of database connections.

    Connections are created lazily and reused. When all connections
    are in use, acquire() blocks or raises PoolExhaustedError.
    """

    def __init__(self, max_size=10, host="localhost", port=5432, timeout=5.0):
        self.max_size = max_size
        self.host = host
        self.port = port
        self.timeout = timeout

        self._available = []
        self._in_use = set()
        self._total_created = 0
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)

        # Metrics (red herring — these are fine)
        self._acquire_count = 0
        self._release_count = 0
        self._timeout_count = 0

    def acquire(self):
        """Acquire a connection from the pool.

        Returns an available connection or creates a new one if under max_size.
        Blocks up to self.timeout seconds, then raises PoolExhaustedError.
        """
        deadline = time.monotonic() + self.timeout

        with self._condition:
            while True:
                # Try to get an available connection
                if self._available:
                    conn = self._available.pop()
                    if conn.is_connected:
                        self._in_use.add(conn.id)
                        self._acquire_count += 1
                        return conn
                    # Dead connection, don't count it
                    self._total_created -= 1
                    continue

                # Create a new one if under limit
                if self._total_created < self.max_size:
                    conn = Connection(self.host, self.port)
                    self._total_created += 1
                    self._in_use.add(conn.id)
                    self._acquire_count += 1
                    return conn

                # Wait for a release
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    self._timeout_count += 1
                    raise PoolExhaustedError(
                        f"No connections available (pool size={self.max_size}, "
                        f"in_use={len(self._in_use)})"
                    )
                self._condition.wait(timeout=remaining)

    def release(self, connection):
        """Return a connection to the pool."""
        with self._condition:
            if connection.id in self._in_use:
                self._in_use.discard(connection.id)
                if connection.is_connected:
                    try:
                        connection.reset()
                    except Exception:
                        # Connection is bad, don't return it
                        self._total_created -= 1
                        self._release_count += 1
                        self._condition.notify()
                        return
                    self._available.append(connection)
                else:
                    self._total_created -= 1
                self._release_count += 1
                self._condition.notify()

    def close_all(self):
        """Close all connections in the pool."""
        with self._lock:
            for conn in self._available:
                conn.close()
            self._available.clear()
            self._in_use.clear()
            self._total_created = 0

    @property
    def available_count(self):
        with self._lock:
            return len(self._available)

    @property
    def in_use_count(self):
        with self._lock:
            return len(self._in_use)

    @property
    def total_created(self):
        with self._lock:
            return self._total_created

    @property
    def stats(self):
        with self._lock:
            return {
                "max_size": self.max_size,
                "total_created": self._total_created,
                "available": len(self._available),
                "in_use": len(self._in_use),
                "acquires": self._acquire_count,
                "releases": self._release_count,
                "timeouts": self._timeout_count,
            }

    def __repr__(self):
        return (
            f"ConnectionPool(max={self.max_size}, "
            f"available={len(self._available)}, "
            f"in_use={len(self._in_use)})"
        )
