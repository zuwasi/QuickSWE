"""Connection pool implementation."""

import threading
import time
from collections import deque
from typing import Any, Callable, Dict, List, Optional


class Connection:
    """Simulates a database / network connection."""

    _counter = 0
    _lock = threading.Lock()

    def __init__(self, dsn: str = "default"):
        with Connection._lock:
            Connection._counter += 1
            self._id = Connection._counter
        self._dsn = dsn
        self._closed = False
        self._created_at = time.monotonic()
        self._last_used = self._created_at

    @property
    def id(self) -> int:
        return self._id

    @property
    def is_closed(self) -> bool:
        return self._closed

    @property
    def dsn(self) -> str:
        return self._dsn

    @property
    def age(self) -> float:
        return time.monotonic() - self._created_at

    def execute(self, query: str) -> str:
        if self._closed:
            raise RuntimeError(f"Connection {self._id} is closed")
        self._last_used = time.monotonic()
        return f"result-{self._id}-{query}"

    def ping(self) -> bool:
        """Health check — returns True if the connection is alive."""
        return not self._closed

    def close(self) -> None:
        self._closed = True

    def __repr__(self):
        status = "closed" if self._closed else "open"
        return f"Connection(id={self._id}, {status})"


class PoolExhaustedError(Exception):
    """Raised when the pool has no available connections."""
    pass


class ConnectionPool:
    """A pool of reusable connections.

    Connections are acquired from the pool and released back after use.
    The pool creates new connections on demand up to max_size.
    """

    def __init__(self, dsn: str = "default", max_size: int = 5,
                 factory: Optional[Callable] = None):
        self._dsn = dsn
        self._max_size = max_size
        self._factory = factory or (lambda: Connection(dsn))
        self._pool: deque = deque()
        self._in_use: Dict[int, Connection] = {}
        self._total_created = 0
        self._lock = threading.Lock()

    @property
    def size(self) -> int:
        return len(self._pool)

    @property
    def in_use_count(self) -> int:
        return len(self._in_use)

    @property
    def total_created(self) -> int:
        return self._total_created

    def acquire(self) -> Connection:
        """Acquire a connection from the pool.

        Returns a pooled connection if available, or creates a new one
        if the pool has not reached max_size.
        """
        with self._lock:
            if self._pool:
                conn = self._pool.popleft()
                self._in_use[conn.id] = conn
                return conn

            total = len(self._pool) + len(self._in_use)
            if total >= self._max_size:
                raise PoolExhaustedError(
                    f"Pool exhausted (max_size={self._max_size})"
                )

            conn = self._factory()
            self._total_created += 1
            self._in_use[conn.id] = conn
            return conn

    def release(self, conn: Connection) -> None:
        """Release a connection back to the pool."""
        with self._lock:
            self._in_use.pop(conn.id, None)
            self._pool.append(conn)

    def close_all(self) -> None:
        """Close all connections in the pool and in use."""
        with self._lock:
            for conn in self._pool:
                conn.close()
            for conn in self._in_use.values():
                conn.close()
            self._pool.clear()
            self._in_use.clear()

    def stats(self) -> dict:
        """Return pool statistics."""
        return {
            "available": len(self._pool),
            "in_use": len(self._in_use),
            "total_created": self._total_created,
            "max_size": self._max_size,
        }

    def prune(self, max_age: float) -> int:
        """Remove connections older than max_age seconds. Returns count removed."""
        removed = 0
        with self._lock:
            new_pool = deque()
            for conn in self._pool:
                if conn.age > max_age:
                    conn.close()
                    removed += 1
                else:
                    new_pool.append(conn)
            self._pool = new_pool
        return removed
