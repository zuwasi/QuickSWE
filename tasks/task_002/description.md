# Task 002: LRU Cache Eviction Bug

## Problem

The `LRUCache` class implements a Least Recently Used cache with a configurable capacity. When the cache is full and a new item is inserted, it should evict the **least recently used** item. However, the current implementation incorrectly evicts the **most recently used** item instead.

## Expected Behavior

- When the cache reaches capacity, the item that was accessed (get or put) least recently should be evicted
- `get()` should mark the accessed item as most recently used
- `put()` should mark the inserted/updated item as most recently used
- After eviction, the evicted key should no longer be accessible

## Files

- `src/lru_cache.py` — LRUCache implementation using OrderedDict
- `tests/test_lru_cache.py` — Test suite
