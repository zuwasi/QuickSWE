"""Tests for LRU cache eviction correctness."""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.lru_cache import LRUCache
from src.hash_map import HashMap
from src.linked_list import DoublyLinkedList, Node


@pytest.mark.fail_to_pass
class TestLRUEvictionOrder:
    """Tests that verify LRU eviction order is correct.

    These tests FAIL because move_to_front doesn't update self.tail
    when the moved node is the current tail. This means self.tail
    still points to the node that's now at the head, so eviction
    removes the wrong item.
    """

    def test_access_lru_item_then_evict(self):
        """Access the LRU item to make it MRU, then add a new item to trigger eviction.

        After accessing the tail (LRU) item, it should move to head (MRU).
        The NEW LRU should be evicted when a new item is added.
        """
        cache = LRUCache(capacity=3)

        cache.put('A', 1)
        cache.put('B', 2)
        cache.put('C', 3)
        # Order: C(MRU), B, A(LRU)

        # Access A (currently LRU/tail) — should move to MRU/head
        val = cache.get('A')
        assert val == 1
        # Expected order: A(MRU), C, B(LRU)

        # Now B should be the LRU
        assert cache.get_lru_key() == 'B', (
            f"Expected LRU key to be 'B', got '{cache.get_lru_key()}'. "
            f"The tail pointer was not updated when A was moved to front."
        )

    def test_eviction_after_tail_move(self):
        """After moving the tail to the front, eviction should remove the correct item."""
        cache = LRUCache(capacity=3)

        cache.put('A', 1)
        cache.put('B', 2)
        cache.put('C', 3)
        # Order: C(MRU), B, A(LRU/tail)

        # Access A (tail) — moves to front
        cache.get('A')
        # Expected order: A(MRU), C, B(LRU)

        # Add D — should evict B (the new LRU)
        cache.put('D', 4)
        # Expected order: D(MRU), A, C(LRU)... wait:
        # After get('A'): A(MRU), C, B(LRU)
        # After put('D'): evict B, then D(MRU), A, C(LRU)

        assert cache.contains('A'), "A was recently accessed, should NOT be evicted"
        assert cache.contains('C'), "C should still be in cache"
        assert cache.contains('D'), "D was just added, should be in cache"
        assert not cache.contains('B'), (
            f"B should have been evicted as LRU, but it's still in cache. "
            f"Keys in cache: {cache.keys()}"
        )

    def test_access_pattern_eviction_correctness(self):
        """Complex access pattern: verify correct eviction after multiple accesses."""
        cache = LRUCache(capacity=3)

        cache.put('A', 1)
        cache.put('B', 2)
        cache.put('C', 3)
        # Order: C(MRU), B, A(LRU)

        # Access A, making it MRU
        cache.get('A')
        # Order: A(MRU), C, B(LRU)

        # Access B, making it MRU
        cache.get('B')
        # Order: B(MRU), A, C(LRU)

        # Add D — should evict C (LRU)
        cache.put('D', 4)
        assert not cache.contains('C'), "C should be evicted as LRU"
        assert cache.contains('A'), "A should still be in cache"
        assert cache.contains('B'), "B should still be in cache"
        assert cache.contains('D'), "D should be in cache"


class TestBasicCacheOperations:
    """Tests for basic cache operations that should always pass."""

    def test_put_and_get(self):
        cache = LRUCache(capacity=5)
        cache.put('key1', 'value1')
        assert cache.get('key1') == 'value1'

    def test_get_missing_key(self):
        cache = LRUCache(capacity=5)
        assert cache.get('missing') is None
        assert cache.get('missing', 'default') == 'default'

    def test_update_existing_key(self):
        cache = LRUCache(capacity=5)
        cache.put('key1', 'v1')
        cache.put('key1', 'v2')
        assert cache.get('key1') == 'v2'
        assert cache.size == 1

    def test_delete_key(self):
        cache = LRUCache(capacity=5)
        cache.put('key1', 'v1')
        assert cache.delete('key1')
        assert cache.get('key1') is None

    def test_cache_capacity(self):
        cache = LRUCache(capacity=3)
        cache.put('A', 1)
        cache.put('B', 2)
        cache.put('C', 3)
        cache.put('D', 4)  # Should evict A
        assert cache.size == 3
        assert not cache.contains('A')

    def test_stats_tracking(self):
        cache = LRUCache(capacity=5)
        cache.put('A', 1)
        cache.get('A')  # hit
        cache.get('B')  # miss
        assert cache.stats.hits == 1
        assert cache.stats.misses == 1


class TestHashMapWorks:
    """Tests that verify the HashMap works correctly.
    These should always pass — the HashMap is NOT the bug.
    """

    def test_basic_operations(self):
        hm = HashMap()
        hm.put('key1', 'val1')
        assert hm.get('key1') == 'val1'
        assert hm.size == 1

    def test_collision_handling(self):
        hm = HashMap(initial_capacity=4)
        for i in range(20):
            hm.put(f'key_{i}', i)
        for i in range(20):
            assert hm.get(f'key_{i}') == i

    def test_remove(self):
        hm = HashMap()
        hm.put('a', 1)
        hm.put('b', 2)
        hm.remove('a')
        assert not hm.contains('a')
        assert hm.get('b') == 2

    def test_resize(self):
        hm = HashMap(initial_capacity=4)
        for i in range(100):
            hm.put(i, i * 10)
        for i in range(100):
            assert hm.get(i) == i * 10
