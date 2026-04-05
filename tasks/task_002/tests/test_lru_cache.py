import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.lru_cache import LRUCache


# ──────────────────────────────────────────────
# pass_to_pass: these must always pass
# ──────────────────────────────────────────────


class TestLRUCacheBasics:
    """Tests for basic cache operations that already work correctly."""

    def test_put_and_get(self):
        cache = LRUCache(3)
        cache.put("a", 1)
        cache.put("b", 2)
        assert cache.get("a") == 1
        assert cache.get("b") == 2

    def test_get_missing_returns_none(self):
        cache = LRUCache(3)
        cache.put("a", 1)
        assert cache.get("z") is None

    def test_update_existing_key(self):
        cache = LRUCache(3)
        cache.put("a", 1)
        cache.put("a", 99)
        assert cache.get("a") == 99
        assert cache.size == 1


# ──────────────────────────────────────────────
# fail_to_pass: these fail before the fix
# ──────────────────────────────────────────────


class TestLRUEviction:
    """Tests for eviction policy — should evict LEAST recently used."""

    @pytest.mark.fail_to_pass
    def test_evicts_least_recently_used(self):
        """With capacity 2, inserting a 3rd item should evict the LRU item."""
        cache = LRUCache(2)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("c", 3)
        assert cache.get("a") is None, "Key 'a' should have been evicted (LRU)"
        assert cache.get("b") == 2
        assert cache.get("c") == 3

    @pytest.mark.fail_to_pass
    def test_get_refreshes_access_order(self):
        """Accessing 'a' makes it MRU, so 'b' becomes LRU and gets evicted."""
        cache = LRUCache(2)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.get("a")  # refresh 'a', now 'b' is LRU
        cache.put("c", 3)  # should evict 'b'
        assert cache.get("b") is None, "'b' should have been evicted as LRU"
        assert cache.get("a") == 1
        assert cache.get("c") == 3

    @pytest.mark.fail_to_pass
    def test_eviction_sequence(self):
        """Multiple evictions should always remove the LRU item."""
        cache = LRUCache(2)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("c", 3)  # evicts 'a'
        assert cache.contains("a") is False
        cache.put("d", 4)  # evicts 'b'
        assert cache.contains("b") is False
        assert cache.get("c") == 3
        assert cache.get("d") == 4
