"""
Database client — high-level interface for database operations.
Uses connection pool, transactions, and retry policy.
"""

from .pool import ConnectionPool, PoolExhaustedError
from .transaction import Transaction, TransactionError
from .retry import RetryPolicy, NoRetry
from .connection import ConnectionError as ConnError


class DatabaseClient:
    """High-level database client.

    Provides a simple interface for executing queries with
    automatic connection management, transactions, and retries.
    """

    def __init__(self, pool=None, retry_policy=None):
        """Initialize the database client.

        Args:
            pool: ConnectionPool instance (created with defaults if None).
            retry_policy: RetryPolicy for retrying failed operations.
        """
        self._pool = pool or ConnectionPool()
        self._retry_policy = retry_policy or NoRetry()
        self._total_queries = 0
        self._total_errors = 0

    def execute(self, query, params=None):
        """Execute a single query with connection management."""
        conn = self._pool.acquire()
        try:
            result = conn.execute(query, params)
            self._total_queries += 1
            return result
        except ConnError:
            self._total_errors += 1
            raise
        finally:
            self._pool.release(conn)

    def execute_in_transaction(self, queries):
        """Execute multiple queries in a single transaction.

        This is the method that triggers the pool leak when things go wrong.
        Each retry attempt acquires a new connection, and if the transaction
        fails in a way that prevents connection release, the pool shrinks.
        """
        def _do_transaction():
            conn = self._pool.acquire()
            # BUG: Transaction.__exit__ may not release the connection
            # if rollback fails, causing a leak. Each retry leaks another
            # connection.
            with Transaction(conn, self._pool) as txn:
                results = []
                for query in queries:
                    if isinstance(query, tuple):
                        results.append(txn.execute(query[0], query[1]))
                    else:
                        results.append(txn.execute(query))
                self._total_queries += len(queries)
                return results

        try:
            return self._retry_policy.execute(_do_transaction)
        except Exception:
            self._total_errors += 1
            raise

    def execute_with_retry(self, query, params=None):
        """Execute a single query with retry policy."""
        def _do_query():
            conn = self._pool.acquire()
            try:
                result = conn.execute(query, params)
                self._total_queries += 1
                return result
            except ConnError:
                self._total_errors += 1
                raise
            finally:
                self._pool.release(conn)

        return self._retry_policy.execute(_do_query)

    @property
    def pool(self):
        return self._pool

    @property
    def stats(self):
        return {
            "total_queries": self._total_queries,
            "total_errors": self._total_errors,
            "pool": self._pool.stats,
        }

    def close(self):
        """Close the client and all pool connections."""
        self._pool.close_all()

    def __repr__(self):
        return f"DatabaseClient(queries={self._total_queries}, errors={self._total_errors})"
