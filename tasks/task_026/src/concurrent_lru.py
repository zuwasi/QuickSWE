"""
Thread-safe LRU cache using OrderedDict and threading.Lock.

Provides get, put, delete, and bulk operations with TTL support.
"""

import threading
import time
from collections import OrderedDict
from typing import Any, Optional, Dict, List, Tuple, Callable


class CacheEntry:
    """Represents a cached value with optional TTL."""

    def __init__(self, value: Any, ttl: Optional[float] = None):
        self.value = value
        self.created_at = time.monotonic()
        self.ttl = ttl
        self.access_count = 0

    def is_expired(self) -> bool:
        if self.ttl is None:
            return False
        return (time.monotonic() - self.created_at) > self.ttl

    def touch(self):
        self.access_count += 1


class ConcurrentLRU:
    """Thread-safe LRU cache with configurable capacity and TTL."""

    def __init__(self, capacity: int, default_ttl: Optional[float] = None):
        if capacity <= 0:
            raise ValueError("Capacity must be positive")
        self.capacity = capacity
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.Lock()
        self._stats = {"hits": 0, "misses": 0, "evictions": 0}

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._cache:
                self._stats["misses"] += 1
                return None
            entry = self._cache[key]
            if entry.is_expired():
                del self._cache[key]
                self._stats["misses"] += 1
                return None
            self._stats["hits"] += 1
            value = entry.value

        entry.touch()
        self._cache.move_to_end(key)
        return value

    def put(self, key: str, value: Any,
            ttl: Optional[float] = None) -> None:
        effective_ttl = ttl if ttl is not None else self.default_ttl
        with self._lock:
            if key in self._cache:
                self._cache[key] = CacheEntry(value, effective_ttl)
                self._cache.move_to_end(key)
            else:
                if len(self._cache) >= self.capacity:
                    self._evict_one()
                self._cache[key] = CacheEntry(value, effective_ttl)

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def _evict_one(self):
        if self._cache:
            evicted_key, _ = self._cache.popitem(last=False)
            self._stats["evictions"] += 1

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    def size(self) -> int:
        with self._lock:
            return len(self._cache)

    def keys(self) -> List[str]:
        with self._lock:
            return list(self._cache.keys())

    def contains(self, key: str) -> bool:
        with self._lock:
            if key not in self._cache:
                return False
            if self._cache[key].is_expired():
                del self._cache[key]
                return False
            return True

    def get_or_compute(self, key: str,
                       factory: Callable[[], Any],
                       ttl: Optional[float] = None) -> Any:
        value = self.get(key)
        if value is not None:
            return value
        computed = factory()
        self.put(key, computed, ttl)
        return computed

    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        result = {}
        for key in keys:
            val = self.get(key)
            if val is not None:
                result[key] = val
        return result

    def put_many(self, items: Dict[str, Any],
                 ttl: Optional[float] = None) -> None:
        for key, value in items.items():
            self.put(key, value, ttl)

    def get_stats(self) -> Dict[str, int]:
        with self._lock:
            return dict(self._stats)

    def evict_expired(self) -> int:
        with self._lock:
            expired_keys = [
                k for k, v in self._cache.items() if v.is_expired()
            ]
            for k in expired_keys:
                del self._cache[k]
            return len(expired_keys)

    def peek(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._cache:
                return None
            entry = self._cache[key]
            if entry.is_expired():
                del self._cache[key]
                return None
            return entry.value

    def get_lru_order(self) -> List[str]:
        with self._lock:
            return list(self._cache.keys())

    def resize(self, new_capacity: int) -> None:
        if new_capacity <= 0:
            raise ValueError("Capacity must be positive")
        with self._lock:
            self.capacity = new_capacity
            while len(self._cache) > self.capacity:
                self._evict_one()
