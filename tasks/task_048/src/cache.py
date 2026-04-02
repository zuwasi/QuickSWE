"""Cache implementation with TTL support."""

from typing import Any, Optional


class Cache:
    """A cache with optional TTL-based expiration.

    Stores key-value pairs with optional time-to-live.
    Expired entries are treated as non-existent.
    """

    def __init__(self):
        self._entries: dict = {}

    def get(self, key: str) -> Any:
        """Get a value from the cache.

        Returns None if not found or expired.
        """
        raise NotImplementedError("Cache.get not yet implemented")

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set a value in the cache with optional TTL.

        Args:
            key: Cache key.
            value: Value to store.
            ttl: Time-to-live in seconds. None means no expiration.
        """
        raise NotImplementedError("Cache.set not yet implemented")

    def delete(self, key: str) -> bool:
        """Delete a key from the cache. Returns True if it existed."""
        raise NotImplementedError("Cache.delete not yet implemented")

    def has(self, key: str) -> bool:
        """Check if a key exists and is not expired."""
        raise NotImplementedError("Cache.has not yet implemented")

    def clear(self) -> None:
        """Remove all entries from the cache."""
        raise NotImplementedError("Cache.clear not yet implemented")

    @property
    def size(self) -> int:
        """Number of (non-expired) entries in the cache."""
        raise NotImplementedError("Cache.size not yet implemented")
