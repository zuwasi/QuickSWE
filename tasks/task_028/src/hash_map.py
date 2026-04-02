"""Custom HashMap with open addressing.

RED HERRING: This implementation uses open addressing with linear probing.
The code is complex but correct. The LRU cache bug is NOT here.
"""

from .key_utils import hash_key, normalize_key


_EMPTY = object()
_DELETED = object()


class HashMapEntry:
    """An entry in the hash map."""

    __slots__ = ('key', 'value', 'hash_value')

    def __init__(self, key, value, hash_value):
        self.key = key
        self.value = value
        self.hash_value = hash_value

    def __repr__(self):
        return f"Entry({self.key!r}: {self.value!r})"


class HashMap:
    """Hash map using open addressing with linear probing.

    This looks complex and potentially buggy, but it handles all
    edge cases correctly including resize, deletion (tombstones),
    and rehashing.
    """

    INITIAL_CAPACITY = 8
    LOAD_FACTOR_THRESHOLD = 0.75
    SHRINK_THRESHOLD = 0.25
    MIN_CAPACITY = 8

    def __init__(self, initial_capacity=None):
        self._capacity = initial_capacity or self.INITIAL_CAPACITY
        self._slots = [_EMPTY] * self._capacity
        self._size = 0
        self._deleted_count = 0

    @property
    def size(self):
        return self._size

    @property
    def capacity(self):
        return self._capacity

    @property
    def load_factor(self):
        return (self._size + self._deleted_count) / self._capacity

    def _find_slot(self, key, hash_value):
        """Find the slot for a key using linear probing.

        Returns (index, found) where found is True if key exists at index.
        This probing logic looks tricky but handles tombstones correctly.
        """
        index = hash_value % self._capacity
        first_deleted = None

        for _ in range(self._capacity):
            slot = self._slots[index]

            if slot is _EMPTY:
                # Empty slot — key doesn't exist
                if first_deleted is not None:
                    return first_deleted, False
                return index, False

            if slot is _DELETED:
                # Tombstone — remember it but keep probing
                if first_deleted is None:
                    first_deleted = index
            elif slot.key == key:
                # Found the key
                return index, True

            index = (index + 1) % self._capacity

        # Table is full (shouldn't happen with proper load factor management)
        if first_deleted is not None:
            return first_deleted, False
        raise RuntimeError("HashMap is full — this should not happen")

    def put(self, key, value):
        """Insert or update a key-value pair."""
        key = normalize_key(key)
        h = hash_key(key)
        index, found = self._find_slot(key, h)

        if found:
            self._slots[index].value = value
        else:
            self._slots[index] = HashMapEntry(key, value, h)
            self._size += 1

            if self.load_factor > self.LOAD_FACTOR_THRESHOLD:
                self._resize(self._capacity * 2)

    def get(self, key, default=None):
        """Get a value by key."""
        key = normalize_key(key)
        h = hash_key(key)
        index, found = self._find_slot(key, h)

        if found:
            return self._slots[index].value
        return default

    def remove(self, key):
        """Remove a key and return its value."""
        key = normalize_key(key)
        h = hash_key(key)
        index, found = self._find_slot(key, h)

        if not found:
            raise KeyError(key)

        value = self._slots[index].value
        self._slots[index] = _DELETED
        self._size -= 1
        self._deleted_count += 1

        # Shrink if too sparse
        if (self._capacity > self.MIN_CAPACITY and
                self._size / self._capacity < self.SHRINK_THRESHOLD):
            self._resize(max(self.MIN_CAPACITY, self._capacity // 2))

        return value

    def contains(self, key):
        """Check if a key exists."""
        key = normalize_key(key)
        h = hash_key(key)
        _, found = self._find_slot(key, h)
        return found

    def _resize(self, new_capacity):
        """Resize the hash map."""
        old_slots = self._slots
        self._capacity = new_capacity
        self._slots = [_EMPTY] * new_capacity
        self._size = 0
        self._deleted_count = 0

        for slot in old_slots:
            if slot is not _EMPTY and slot is not _DELETED:
                self.put(slot.key, slot.value)

    def keys(self):
        """Return all keys."""
        return [
            slot.key for slot in self._slots
            if slot is not _EMPTY and slot is not _DELETED
        ]

    def values(self):
        """Return all values."""
        return [
            slot.value for slot in self._slots
            if slot is not _EMPTY and slot is not _DELETED
        ]

    def items(self):
        """Return all key-value pairs."""
        return [
            (slot.key, slot.value) for slot in self._slots
            if slot is not _EMPTY and slot is not _DELETED
        ]

    def __len__(self):
        return self._size

    def __contains__(self, key):
        return self.contains(key)

    def __repr__(self):
        items = ', '.join(f'{k!r}: {v!r}' for k, v in self.items())
        return f"HashMap({{{items}}})"
