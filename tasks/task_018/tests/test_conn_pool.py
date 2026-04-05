import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.conn_pool import Connection, ConnectionPool, PoolExhaustedError


# ─── fail_to_pass ───────────────────────────────────────────────

@pytest.mark.fail_to_pass
def test_acquire_skips_closed_connection():
    """acquire() must not return a connection that was closed before release."""
    pool = ConnectionPool(max_size=5)
    conn = pool.acquire()
    conn.close()
    pool.release(conn)

    conn2 = pool.acquire()
    assert not conn2.is_closed, "Pool returned a closed connection"
    assert conn2.id != conn.id


@pytest.mark.fail_to_pass
def test_release_rejects_closed_connection():
    """release() should discard a closed connection instead of pooling it."""
    pool = ConnectionPool(max_size=5)
    c1 = pool.acquire()
    c1.close()
    pool.release(c1)

    assert pool.size == 0, "Closed connection should not be in the pool"


@pytest.mark.fail_to_pass
def test_acquired_connection_is_usable():
    """Every connection from acquire() must respond to execute()."""
    pool = ConnectionPool(max_size=2)

    c1 = pool.acquire()
    c1.close()
    pool.release(c1)

    c2 = pool.acquire()
    result = c2.execute("SELECT 1")
    assert "result" in result


# ─── pass_to_pass ───────────────────────────────────────────────

def test_basic_acquire_release():
    """Acquire and release cycle works."""
    pool = ConnectionPool(max_size=3)
    conn = pool.acquire()
    assert not conn.is_closed
    pool.release(conn)
    assert pool.size == 1


def test_pool_exhausted():
    """Exceeding max_size raises PoolExhaustedError."""
    pool = ConnectionPool(max_size=1)
    pool.acquire()
    with pytest.raises(PoolExhaustedError):
        pool.acquire()


def test_close_all():
    """close_all shuts down every connection."""
    pool = ConnectionPool(max_size=3)
    c1 = pool.acquire()
    c2 = pool.acquire()
    pool.release(c1)
    pool.close_all()
    assert c1.is_closed
    assert c2.is_closed
    assert pool.size == 0
