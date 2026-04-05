# Task 026: Concurrent LRU Cache Race Condition

## Problem

A thread-safe LRU cache has a race condition in its `get()` method. The method
acquires the lock to read the value, releases the lock, and then tries to call
`move_to_end()` on the OrderedDict without holding the lock. Under concurrent
access, this corrupts the LRU ordering and can cause KeyError exceptions.

## Expected Behavior

All cache operations should be fully atomic. The `get()` method should hold the
lock for the entire duration of the read-and-reorder operation.

## Files

- `src/concurrent_lru.py` — Thread-safe LRU cache using OrderedDict and Lock
