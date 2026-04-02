"""Cache statistics tracking."""

import time


class CacheStats:
    """Tracks cache performance statistics."""

    def __init__(self):
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._insertions = 0
        self._updates = 0
        self._deletions = 0
        self._start_time = time.time()
        self._last_access_time = None
        self._hit_keys = []
        self._miss_keys = []
        self._evicted_keys = []

    @property
    def hits(self):
        return self._hits

    @property
    def misses(self):
        return self._misses

    @property
    def evictions(self):
        return self._evictions

    @property
    def insertions(self):
        return self._insertions

    @property
    def total_requests(self):
        return self._hits + self._misses

    @property
    def hit_rate(self):
        total = self.total_requests
        if total == 0:
            return 0.0
        return self._hits / total

    @property
    def miss_rate(self):
        return 1.0 - self.hit_rate

    def record_hit(self, key=None):
        self._hits += 1
        self._last_access_time = time.time()
        if key is not None:
            self._hit_keys.append(key)

    def record_miss(self, key=None):
        self._misses += 1
        self._last_access_time = time.time()
        if key is not None:
            self._miss_keys.append(key)

    def record_eviction(self, key=None):
        self._evictions += 1
        if key is not None:
            self._evicted_keys.append(key)

    def record_insertion(self):
        self._insertions += 1

    def record_update(self):
        self._updates += 1

    def record_deletion(self):
        self._deletions += 1

    def get_recent_evictions(self, n=10):
        """Return the n most recent evicted keys."""
        return self._evicted_keys[-n:]

    def get_recent_hits(self, n=10):
        """Return the n most recent hit keys."""
        return self._hit_keys[-n:]

    def get_recent_misses(self, n=10):
        """Return the n most recent missed keys."""
        return self._miss_keys[-n:]

    def reset(self):
        """Reset all statistics."""
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._insertions = 0
        self._updates = 0
        self._deletions = 0
        self._start_time = time.time()
        self._last_access_time = None
        self._hit_keys.clear()
        self._miss_keys.clear()
        self._evicted_keys.clear()

    def summary(self):
        """Return a summary dict."""
        return {
            'hits': self._hits,
            'misses': self._misses,
            'hit_rate': f"{self.hit_rate:.2%}",
            'evictions': self._evictions,
            'insertions': self._insertions,
            'updates': self._updates,
            'uptime': time.time() - self._start_time,
        }

    def __repr__(self):
        return (
            f"CacheStats(hits={self._hits}, misses={self._misses}, "
            f"evictions={self._evictions}, hit_rate={self.hit_rate:.2%})"
        )
