"""Thread-safe cache implementation using a dictionary and threading lock."""

import threading
import time


class ThreadSafeCache:
    """A cache that provides thread-safe get/set/delete operations."""

    def __init__(self, max_size=1000):
        self._store = {}
        self._lock = threading.Lock()
        self._max_size = max_size
        self._access_order = []

    def get(self, key):
        """Retrieve a value from the cache. Returns None if not found."""
        with self._lock:
            if key in self._store:
                # Update access order for LRU
                if key in self._access_order:
                    self._access_order.remove(key)
                self._access_order.append(key)
                return self._store[key]
            return None

    def set(self, key, value):
        """Store a value in the cache."""
        with self._lock:
            if len(self._store) >= self._max_size and key not in self._store:
                self._evict()
            self._store[key] = value
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)

    def delete(self, key):
        """Remove a key from the cache."""
        with self._lock:
            if key in self._store:
                del self._store[key]
                self._access_order.remove(key)
                return True
            return False

    def has(self, key):
        """Check if a key exists in the cache."""
        with self._lock:
            return key in self._store

    def clear(self):
        """Remove all entries from the cache."""
        with self._lock:
            self._store.clear()
            self._access_order.clear()

    def size(self):
        """Return the number of items in the cache."""
        with self._lock:
            return len(self._store)

    def _evict(self):
        """Evict the least recently used entry. Must be called while holding _lock."""
        if self._access_order:
            oldest_key = self._access_order.pop(0)
            del self._store[oldest_key]
