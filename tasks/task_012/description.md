# Task 012 – Memoization Decorator Returns Stale Results

## Problem
The `memoize` decorator caches function results keyed by their arguments.
When a mutable argument (e.g. a list) is passed, the decorator stores the
list object reference as part of the cache key. If the caller later mutates
that list object and calls the function again, the cache returns the stale
result from the first call because the key object is the same identity.

## Expected Behaviour
- Arguments should be frozen (deep-copied / converted to hashable form)
  before being used as cache keys.
- Mutating a list after a call must not affect future cache lookups.
- The decorator should still work correctly for immutable arguments.

## Files
- `src/memoize.py` – the buggy decorator
- `tests/test_memoize.py` – test suite
