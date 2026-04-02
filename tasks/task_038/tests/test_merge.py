"""Tests for the k-way merge iterator pipeline."""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.sorted_iterator import SortedIterator
from src.heap import MinHeap
from src.merge_iterator import MergeIterator
from src.stream_processor import StreamProcessor


# ── pass-to-pass: these must always pass ─────────────────────────────────

class TestSortedIteratorBasics:
    """Basic SortedIterator operations."""

    def test_sorted_iterator_basics(self):
        it = SortedIterator([1, 3, 5, 7], source_name="test")
        assert it.has_next
        assert it.peek() == 1
        assert it.next() == 1
        assert it.peek() == 3
        assert it.remaining == 3
        assert it.consumed == 1

        remaining = it.collect_remaining()
        assert remaining == [3, 5, 7]
        assert not it.has_next
        assert it.next() is None

        # Empty iterator
        empty = SortedIterator.empty()
        assert not empty.has_next
        assert empty.peek() is None

        # From range
        r = SortedIterator.from_range(0, 5)
        assert r.collect_remaining() == [0, 1, 2, 3, 4]


class TestHeapOperations:
    """MinHeap works correctly with comparable elements."""

    def test_heap_operations(self):
        heap = MinHeap()
        assert heap.is_empty

        # Push integers (which are fully comparable)
        heap.push(5)
        heap.push(2)
        heap.push(8)
        heap.push(1)

        assert heap.size == 4
        assert heap.peek() == 1
        assert heap.pop() == 1
        assert heap.pop() == 2

        # Push-pop
        result = heap.push_pop(3)
        assert result == 3  # 3 < 5, so 3 is returned immediately

        result = heap.push_pop(10)
        assert result == 5  # 5 is smallest, returned; 10 inserted

        # Drain
        remaining = heap.to_sorted_list()
        assert remaining == [8, 10]


class TestMergeDistinctValues:
    """Merging iterators with no overlapping values works."""

    def test_merge_distinct_values(self):
        # No duplicates across iterators — no comparator issue
        it1 = SortedIterator([1, 4, 7])
        it2 = SortedIterator([2, 5, 8])
        it3 = SortedIterator([3, 6, 9])

        merger = MergeIterator([it1, it2, it3])
        result = merger.collect_all()
        assert result == [1, 2, 3, 4, 5, 6, 7, 8, 9]
        assert merger.total_emitted == 9


# ── fail-to-pass: these FAIL with the bug, PASS after fix ────────────────

class TestMergeDuplicateValues:
    """Merging iterators with duplicate values across sources."""

    @pytest.mark.fail_to_pass
    def test_merge_with_duplicate_values(self):
        """When two iterators have the same value, the merge must not crash
        or produce incorrect ordering.

        BUG: heap compares (value, SortedIterator) tuples. When values
        are equal, it tries SortedIterator < SortedIterator which raises
        TypeError because __lt__ is not defined.
        """
        it1 = SortedIterator([1, 3, 5, 7], source_name="a")
        it2 = SortedIterator([2, 3, 5, 8], source_name="b")
        it3 = SortedIterator([3, 5, 6, 9], source_name="c")

        merger = MergeIterator([it1, it2, it3])
        result = merger.collect_all()

        # Must be sorted
        for i in range(1, len(result)):
            assert result[i] >= result[i - 1], (
                f"Output not sorted at index {i}: "
                f"{result[i-1]} > {result[i]}"
            )

        # Must contain all values
        expected = sorted([1, 3, 5, 7, 2, 3, 5, 8, 3, 5, 6, 9])
        assert result == expected


class TestMergeManyOverlapping:
    """Merging many iterators with heavily overlapping ranges."""

    @pytest.mark.fail_to_pass
    def test_merge_many_iterators_with_overlapping_ranges(self):
        """5 iterators all containing overlapping ranges trigger repeated
        tie-breaking in the heap."""
        lists = [
            [1, 2, 3, 4, 5],
            [2, 3, 4, 5, 6],
            [3, 4, 5, 6, 7],
            [4, 5, 6, 7, 8],
            [5, 6, 7, 8, 9],
        ]

        merger = MergeIterator.from_lists(*lists)
        result = merger.collect_all()

        expected = sorted(sum(lists, []))
        assert result == expected, (
            f"Merged output is not correctly sorted: {result}"
        )

        # Verify strict ordering
        for i in range(1, len(result)):
            assert result[i] >= result[i - 1]


class TestStreamProcessorIdentical:
    """StreamProcessor with identical streams must not crash."""

    @pytest.mark.fail_to_pass
    def test_stream_processor_identical_streams(self):
        """Three identical streams: every value triggers a tie."""
        processor = StreamProcessor()
        for i in range(3):
            processor.add_stream([10, 20, 30, 40, 50], source_name=f"copy_{i}")

        result, stats = processor.merge_with_stats()

        assert len(result) == 15  # 5 values × 3 streams
        assert result == sorted(result), "Output must be sorted"
        assert stats.total_items == 15
        assert stats.min_value == 10
        assert stats.max_value == 50

        # Verify sorting
        is_sorted, fail_idx = processor.verify_sorted(result)
        assert is_sorted, f"Not sorted at index {fail_idx}"
