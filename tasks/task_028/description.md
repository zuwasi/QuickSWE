# Bug Report: LRU Cache Evicts Wrong Items

## Summary

Our custom LRU cache implementation appears to evict recently-accessed items under certain conditions, violating the "least recently used" eviction policy.

## Steps to Reproduce

1. Create an LRU cache with a small capacity (e.g., 3)
2. Add items up to capacity
3. Access one of the items (making it "recently used")
4. Add a new item (should evict the LEAST recently used)
5. The wrong item gets evicted — sometimes the one we just accessed gets kicked out

## Expected Behavior

After accessing an item, it should be moved to the "most recently used" position and should be the LAST item to be evicted.

## Actual Behavior

Items that were just accessed are sometimes evicted instead of items that haven't been accessed. This seems to happen particularly when:
- The cache has only a few items
- An item is accessed and then a new item is immediately inserted

## Environment

- Python 3.10+
- No external dependencies

## Additional Notes

- The custom HashMap implementation is complex and uses open addressing — could that be causing issues?
- The cache statistics (hits/misses) seem to be counted correctly
- We use a doubly-linked list internally, which is the standard approach for LRU
- The bug seems intermittent but we've found a reproducible pattern with small caches
