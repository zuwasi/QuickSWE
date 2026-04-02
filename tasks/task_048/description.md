# Refactoring: Add Caching Layer with Invalidation to Repository Pattern

## Summary

The existing `UserRepository` works correctly but hits the storage backend on every call. We need a transparent caching layer (`CachedRepository`) that wraps any repository, caches `get_by_id` results, invalidates on updates/deletes, and supports TTL-based expiration. The original `Repository` interface must remain unchanged.

## Current State

- `src/repository.py`: `UserRepository` with `get_by_id`, `get_all`, `create`, `update`, `delete` — all work but hit `InMemoryStorage` on every call.
- `src/storage.py`: `InMemoryStorage` with dict-based backend.
- `src/model.py`: `User` model with `id`, `name`, `email`, `created_at`.
- `src/cache.py`: Stub `Cache` class with `get`, `set`, `delete`, `clear` — all raise `NotImplementedError`.

## Requirements

### Cache (`src/cache.py`)
1. Implement `get(key) -> value | None` — return cached value or None.
2. Implement `set(key, value, ttl=None)` — store with optional TTL in seconds.
3. Implement `delete(key) -> bool` — remove from cache.
4. Implement `clear()` — remove all entries.
5. Implement `has(key) -> bool` — check existence (respecting TTL).
6. Expired entries should be treated as non-existent.

### CachedRepository (`src/repository.py` or new wrapper)
1. Wrap any `UserRepository` transparently.
2. Same interface: `get_by_id`, `get_all`, `create`, `update`, `delete`.
3. `get_by_id` checks cache first; on miss, fetches from wrapped repo and caches.
4. `update` invalidates the cache for that ID, then delegates to wrapped repo.
5. `delete` invalidates the cache for that ID, then delegates.
6. `create` delegates to wrapped repo (no caching needed for new entities).
7. Support configurable TTL (default or per-operation).

### Backward Compatibility
- `UserRepository` must continue to work exactly as before.
- `CachedRepository` should be a drop-in replacement.

## Acceptance Criteria
- CachedRepository caches reads: second `get_by_id` for same ID doesn't hit storage.
- CachedRepository invalidates on write: `update`/`delete` clears cached entry.
- TTL expiration: cached entry expires after TTL seconds.
- UserRepository CRUD continues to work unchanged.
