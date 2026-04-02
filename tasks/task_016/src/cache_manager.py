"""Cache manager providing higher-level caching operations."""

import time
import threading
from .cache import ThreadSafeCache


class CacheEntry:
    """Wraps a cached value with metadata."""

    def __init__(self, value, ttl=None):
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl

    def is_expired(self):
        if self.ttl is None:
            return False
        return (time.time() - self.created_at) > self.ttl


class CacheManager:
    """High-level cache manager that supports compute-on-miss and TTL."""

    def __init__(self, default_ttl=None, max_size=1000):
        self._cache = ThreadSafeCache(max_size=max_size)
        self._default_ttl = default_ttl
        self._stats = {"hits": 0, "misses": 0, "computations": 0}
        self._stats_lock = threading.Lock()

    def get_or_compute(self, key, compute_func, ttl=None):
        """Get a value from cache, or compute and store it if missing.

        This is the primary interface. If the key is not in cache (or has
        expired), ``compute_func`` is called to produce the value, which
        is then cached before being returned.

        Args:
            key: Cache key.
            compute_func: Callable that produces the value (may be expensive).
            ttl: Optional time-to-live in seconds (overrides default).

        Returns:
            The cached or freshly computed value.
        """
        # Step 1: check if already cached
        entry = self._cache.get(key)
        if entry is not None and not entry.is_expired():
            with self._stats_lock:
                self._stats["hits"] += 1
            return entry.value

        # Step 2: compute the value (expensive)
        with self._stats_lock:
            self._stats["misses"] += 1
            self._stats["computations"] += 1
        value = compute_func()

        # Step 3: store in cache
        effective_ttl = ttl if ttl is not None else self._default_ttl
        entry = CacheEntry(value, ttl=effective_ttl)
        self._cache.set(key, entry)

        return value

    def invalidate(self, key):
        """Remove a key from the cache."""
        return self._cache.delete(key)

    def clear(self):
        """Clear the entire cache."""
        self._cache.clear()
        with self._stats_lock:
            self._stats = {"hits": 0, "misses": 0, "computations": 0}

    def get_stats(self):
        """Return cache statistics."""
        with self._stats_lock:
            return dict(self._stats)

    def cache_size(self):
        """Return current cache size."""
        return self._cache.size()
