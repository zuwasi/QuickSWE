"""
LRU (Least Recently Used) Cache implementation.

Uses an OrderedDict to maintain access order. Items are moved to the
end of the dict when accessed, and eviction removes from one end
when capacity is exceeded.
"""

from collections import OrderedDict


class LRUCache:
    """A cache that evicts the least recently used item when full."""

    def __init__(self, capacity):
        """Initialize the cache with a given capacity.

        Args:
            capacity: Maximum number of items the cache can hold.
                      Must be a positive integer.

        Raises:
            ValueError: If capacity is not a positive integer.
        """
        if not isinstance(capacity, int) or capacity <= 0:
            raise ValueError("Capacity must be a positive integer")
        self._capacity = capacity
        self._cache = OrderedDict()
        self._hits = 0
        self._misses = 0

    @property
    def capacity(self):
        """Return the maximum capacity of the cache."""
        return self._capacity

    @property
    def size(self):
        """Return the current number of items in the cache."""
        return len(self._cache)

    @property
    def hit_rate(self):
        """Return the cache hit rate as a float between 0 and 1."""
        total = self._hits + self._misses
        if total == 0:
            return 0.0
        return self._hits / total

    def get(self, key):
        """Retrieve an item from the cache.

        Moves the accessed item to the most-recently-used position.

        Args:
            key: The key to look up.

        Returns:
            The cached value, or None if the key is not found.
        """
        if key not in self._cache:
            self._misses += 1
            return None
        self._hits += 1
        self._cache.move_to_end(key)
        return self._cache[key]

    def put(self, key, value):
        """Insert or update an item in the cache.

        If the cache is at capacity and the key is new, the least
        recently used item is evicted first.

        Args:
            key: The key for the item.
            value: The value to cache.
        """
        if key in self._cache:
            self._cache.move_to_end(key)
            self._cache[key] = value
            return

        if len(self._cache) >= self._capacity:
            self._cache.move_to_end(key)
            self._cache.popitem(last=True)

        self._cache[key] = value

    def delete(self, key):
        """Remove an item from the cache.

        Args:
            key: The key to remove.

        Returns:
            True if the key was found and removed, False otherwise.
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def contains(self, key):
        """Check if a key exists in the cache without updating access order."""
        return key in self._cache

    def peek(self, key):
        """Get a value without updating access order.

        Args:
            key: The key to look up.

        Returns:
            The cached value, or None if not found.
        """
        return self._cache.get(key)

    def clear(self):
        """Remove all items from the cache and reset stats."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    def keys(self):
        """Return cache keys in order from least to most recently used."""
        return list(self._cache.keys())

    def __repr__(self):
        items = ", ".join(f"{k}: {v}" for k, v in self._cache.items())
        return f"LRUCache(capacity={self._capacity}, items={{{items}}})"

    def __len__(self):
        return len(self._cache)
