"""Key hashing utilities for the cache."""


def hash_key(key):
    """Hash a key for use in the hash map.

    Supports string, int, float, tuple, and frozenset keys.
    """
    if isinstance(key, int):
        return key
    elif isinstance(key, str):
        h = 0
        for char in key:
            h = (h * 31 + ord(char)) & 0xFFFFFFFF
        return h
    elif isinstance(key, float):
        if key != key:  # NaN
            return 0
        return hash_key(str(key))
    elif isinstance(key, tuple):
        h = 0
        for item in key:
            h = (h * 37 + hash_key(item)) & 0xFFFFFFFF
        return h
    elif isinstance(key, frozenset):
        h = 0
        for item in sorted(key, key=str):
            h = (h * 41 + hash_key(item)) & 0xFFFFFFFF
        return h
    else:
        return hash(key) & 0xFFFFFFFF


def normalize_key(key):
    """Normalize a key to ensure consistent hashing."""
    if isinstance(key, bool):
        return int(key)
    if isinstance(key, float) and key.is_integer():
        return int(key)
    return key


def validate_key(key):
    """Validate that a key is hashable."""
    try:
        hash(key)
        return True
    except TypeError:
        return False


class KeyWrapper:
    """Wraps a key with pre-computed hash for O(1) comparisons in hash map."""

    __slots__ = ('key', '_hash')

    def __init__(self, key):
        self.key = normalize_key(key)
        self._hash = hash_key(self.key)

    def __hash__(self):
        return self._hash

    def __eq__(self, other):
        if isinstance(other, KeyWrapper):
            return self.key == other.key
        return self.key == other

    def __repr__(self):
        return f"KeyWrapper({self.key!r})"
