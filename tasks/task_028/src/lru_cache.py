"""LRU Cache implementation using a doubly-linked list and dict."""

from .linked_list import DoublyLinkedList, Node
from .cache_stats import CacheStats


class LRUCache:
    """Least Recently Used cache with O(1) get and put.

    Uses a doubly-linked list to maintain access order and a Python dict
    for O(1) key lookups. Head of the list = most recently used,
    tail = least recently used.
    """

    def __init__(self, capacity):
        if capacity < 1:
            raise ValueError("Capacity must be at least 1")
        self._capacity = capacity
        self._map = {}  # key -> Node
        self._list = DoublyLinkedList()
        self._stats = CacheStats()

    @property
    def capacity(self):
        return self._capacity

    @property
    def size(self):
        return len(self._map)

    @property
    def stats(self):
        return self._stats

    def get(self, key, default=None):
        """Get a value from the cache.

        If found, moves the item to the front (most recently used).
        """
        if key not in self._map:
            self._stats.record_miss(key)
            return default

        node = self._map[key]
        # Move to front to mark as recently used
        # BUG: _move_to_front calls list.move_to_front which does
        # remove + push_front even when node is the only element,
        # causing head/tail to become None momentarily
        self._move_to_front(node)
        self._stats.record_hit(key)
        return node.value

    def put(self, key, value):
        """Put a value in the cache.

        If the key exists, update the value and move to front.
        If the cache is full, evict the least recently used item.
        """
        if key in self._map:
            node = self._map[key]
            node.value = value
            self._move_to_front(node)
            self._stats.record_update()
            return

        # Check if we need to evict
        if len(self._map) >= self._capacity:
            self._evict_lru()

        # Insert new node
        node = Node(key, value)
        self._map[key] = node
        self._list.push_front(node)
        self._stats.record_insertion()

    def delete(self, key):
        """Remove a key from the cache."""
        if key not in self._map:
            return False

        node = self._map.pop(key)
        self._list.remove(node)
        self._stats.record_deletion()
        return True

    def contains(self, key):
        """Check if a key exists without affecting access order."""
        return key in self._map

    def peek(self, key, default=None):
        """Get a value without updating access order."""
        if key not in self._map:
            return default
        return self._map[key].value

    def _move_to_front(self, node):
        """Move a node to the front of the access list."""
        self._list.move_to_front(node)

    def _evict_lru(self):
        """Evict the least recently used item."""
        tail = self._list.remove_tail()
        if tail is not None:
            del self._map[tail.key]
            self._stats.record_eviction(tail.key)

    def get_access_order(self):
        """Return keys in access order (MRU first, LRU last)."""
        return self._list.keys()

    def get_lru_key(self):
        """Return the least recently used key."""
        tail = self._list.peek_tail()
        return tail.key if tail else None

    def get_mru_key(self):
        """Return the most recently used key."""
        head = self._list.peek_front()
        return head.key if head else None

    def clear(self):
        """Clear the entire cache."""
        self._map.clear()
        while not self._list.is_empty:
            self._list.remove_tail()
        self._stats.reset()

    def items(self):
        """Return all items in access order (MRU first)."""
        return [(node.key, node.value) for node in self._list.to_list()]

    def keys(self):
        """Return all keys in access order (MRU first)."""
        return self._list.keys()

    def values(self):
        """Return all values in access order (MRU first)."""
        return [node.value for node in self._list.to_list()]

    def __len__(self):
        return self.size

    def __contains__(self, key):
        return self.contains(key)

    def __repr__(self):
        items = ', '.join(f'{k!r}: {v!r}' for k, v in self.items())
        return f"LRUCache(cap={self._capacity}, {{{items}}})"
