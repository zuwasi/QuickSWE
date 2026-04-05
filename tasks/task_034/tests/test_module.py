import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.merge_heap import MergeableHeap, merge_k_heaps, k_way_merge_sorted


class TestMergeableHeapPassToPass:
    """Tests that should pass both before and after the fix."""

    def test_insert_and_extract(self):
        heap = MergeableHeap()
        heap.insert(5)
        heap.insert(3)
        heap.insert(7)
        assert heap.extract_min().key == 3
        assert heap.extract_min().key == 5

    def test_from_list(self):
        heap = MergeableHeap.from_list([(3, "c"), (1, "a"), (2, "b")])
        assert heap.extract_min().key == 1
        assert heap.extract_min().key == 2

    def test_k_way_merge(self):
        result = k_way_merge_sorted([[1, 4, 7], [2, 5, 8], [3, 6, 9]])
        assert result == list(range(1, 10))


@pytest.mark.fail_to_pass
class TestMergeableHeapFailToPass:
    """Tests that fail before the fix and pass after."""

    def test_merge_produces_valid_heap(self):
        h1 = MergeableHeap()
        for v in [10, 30, 50, 70]:
            h1.insert(v)

        h2 = MergeableHeap()
        for v in [20, 40, 60, 80]:
            h2.insert(v)

        merged = h1.merge(h2)
        assert merged.is_valid_heap()

    def test_merge_extract_sorted(self):
        h1 = MergeableHeap.from_list([(5, "a"), (15, "b"), (25, "c")])
        h2 = MergeableHeap.from_list([(10, "d"), (20, "e"), (30, "f")])
        merged = h1.merge(h2)
        extracted = []
        while not merged.is_empty():
            extracted.append(merged.extract_min().key)
        assert extracted == sorted(extracted)
        assert extracted == [5, 10, 15, 20, 25, 30]

    def test_from_list_large_produces_valid_heap(self):
        items = [(v, str(v)) for v in [90, 10, 50, 30, 70, 20, 80, 40, 60]]
        h = MergeableHeap.from_list(items)
        assert h.is_valid_heap(), f"from_list produced invalid heap: {h.get_keys()}"
        result = h.to_sorted_list()
        keys = [k for k, _ in result]
        assert keys == sorted(keys)
