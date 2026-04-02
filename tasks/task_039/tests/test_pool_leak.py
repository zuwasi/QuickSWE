"""Tests for connection pool leak under error conditions."""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.pool import ConnectionPool, PoolExhaustedError
from src.connection import Connection
from src.transaction import Transaction, TransactionError
from src.retry import RetryPolicy, NoRetry
from src.client import DatabaseClient


# ── pass-to-pass: these must always pass ─────────────────────────────────

class TestPoolBasicAcquireRelease:
    """Basic pool operations work correctly."""

    def test_pool_basic_acquire_release(self):
        pool = ConnectionPool(max_size=3, timeout=1.0)

        c1 = pool.acquire()
        c2 = pool.acquire()
        assert pool.in_use_count == 2
        assert pool.available_count == 0

        pool.release(c1)
        assert pool.in_use_count == 1
        assert pool.available_count == 1

        pool.release(c2)
        assert pool.in_use_count == 0
        assert pool.available_count == 2

        # Re-acquire reuses released connection
        c3 = pool.acquire()
        assert pool.available_count == 1  # one still available

        pool.release(c3)
        pool.close_all()


class TestConnectionExecute:
    """Connection execute works."""

    def test_connection_execute(self):
        conn = Connection()
        result = conn.execute("SELECT 1")
        assert result["status"] == "ok"
        assert conn.is_connected

        conn.close()
        assert not conn.is_connected
        with pytest.raises(Exception):
            conn.execute("SELECT 1")


class TestTransactionHappyPath:
    """Transaction works when nothing goes wrong."""

    def test_transaction_happy_path(self):
        pool = ConnectionPool(max_size=2, timeout=1.0)
        conn = pool.acquire()

        with Transaction(conn, pool) as txn:
            txn.execute("INSERT INTO t VALUES (1)")
            txn.execute("INSERT INTO t VALUES (2)")

        # Connection should be released back
        assert pool.in_use_count == 0
        assert pool.available_count == 1
        pool.close_all()


# ── fail-to-pass: these FAIL with the bug, PASS after fix ────────────────

class TestPoolNotExhausted:
    """Pool should not be exhausted after transaction errors."""

    @pytest.mark.fail_to_pass
    def test_pool_not_exhausted_after_errors(self):
        """After multiple failed transactions, the pool should still have
        all its connections available.

        BUG: Each failed transaction that triggers a rollback failure
        leaks a connection. After max_size failures, the pool is exhausted.
        """
        pool = ConnectionPool(max_size=3, timeout=0.5)

        for i in range(5):
            conn = pool.acquire()
            conn._fail_on_rollback = True

            try:
                with Transaction(conn, pool) as txn:
                    txn.execute("INSERT INTO t VALUES (?)", (i,))
                    raise ValueError(f"Simulated app error #{i}")
            except (ValueError, TransactionError):
                pass

        # BUG: after the above loop, all 3 connections are leaked
        # because rollback fails and release is never called
        # The pool should still be usable
        assert pool.in_use_count == 0, (
            f"Pool has {pool.in_use_count} connections still in use — "
            f"they were leaked"
        )

        # Should be able to acquire a connection
        try:
            conn = pool.acquire()
            pool.release(conn)
        except PoolExhaustedError:
            pytest.fail(
                "Pool is exhausted — connections were leaked on "
                "rollback failures"
            )

        pool.close_all()


class TestConnectionReturnedOnRollbackFailure:
    """Connection must be returned to pool even if rollback fails."""

    @pytest.mark.fail_to_pass
    def test_connection_returned_on_rollback_failure(self):
        """When Transaction.__exit__ catches an exception and tries to
        rollback, but rollback itself raises, the connection MUST still
        be returned to the pool.
        """
        pool = ConnectionPool(max_size=1, timeout=0.5)
        conn = pool.acquire()
        conn._fail_on_rollback = True

        try:
            with Transaction(conn, pool) as txn:
                txn.execute("DO SOMETHING")
                raise RuntimeError("Application error")
        except (RuntimeError, TransactionError):
            pass

        # The single connection must be back in the pool
        assert pool.in_use_count == 0, (
            f"Connection was not returned to pool "
            f"(in_use={pool.in_use_count})"
        )

        # Must be able to acquire again
        try:
            conn2 = pool.acquire()
            pool.release(conn2)
        except PoolExhaustedError:
            pytest.fail("Pool exhausted — connection leaked on rollback failure")

        pool.close_all()


class TestClientRetryDoesNotLeak:
    """Client with retry policy must not leak connections."""

    @pytest.mark.fail_to_pass
    def test_client_execute_with_retry_does_not_leak(self):
        """When execute_in_transaction is retried, each failed attempt
        must not leak a connection.

        BUG: Each retry acquires a new connection. If the transaction
        fails with a rollback error, that connection is leaked. After
        max_retries leaked connections, the pool is exhausted.
        """
        pool = ConnectionPool(max_size=5, timeout=0.5)
        retry = RetryPolicy(max_retries=2, retry_on=(Exception,))
        client = DatabaseClient(pool=pool, retry_policy=retry)

        # Make connections fail on rollback to trigger the leak.
        # The execute() succeeds but we force an app-level exception
        # inside the transaction, so __exit__ tries to rollback.
        original_acquire = pool.acquire
        attempt = [0]

        def patched_acquire():
            conn = original_acquire()
            conn._fail_on_rollback = True
            attempt[0] += 1
            return conn

        pool.acquire = patched_acquire

        # Patch execute_in_transaction to raise inside the txn body,
        # triggering rollback path in __exit__
        original_exec_in_txn = client.execute_in_transaction

        def failing_transaction(queries):
            conn = pool.acquire()
            with Transaction(conn, pool) as txn:
                txn.execute("SELECT 1")
                raise RuntimeError("Simulated failure inside transaction")

        try:
            retry.execute(failing_transaction, ["SELECT 1"])
        except Exception:
            pass

        # Restore
        pool.acquire = original_acquire

        # All connections should be returned regardless of errors
        assert pool.in_use_count == 0, (
            f"Pool has {pool.in_use_count} leaked connections after "
            f"{attempt[0]} retry attempts"
        )

        pool.close_all()
