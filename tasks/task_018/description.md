# Task 018 – Connection Pool Returns Closed Connections

## Problem
The `ConnectionPool` returns connections to callers via `acquire()` and
accepts them back with `release()`. When a connection is closed (either
explicitly or due to an error) and then released back to the pool, the
pool does not check the connection's health before handing it out to the
next caller.

## Expected Behaviour
- `acquire()` must never return a closed connection.
- If a closed connection is at the front of the pool, it must be discarded
  and a new one created.
- `release()` should only put healthy connections back.

## Files
- `src/conn_pool.py` – the buggy pool
- `tests/test_conn_pool.py` – test suite
