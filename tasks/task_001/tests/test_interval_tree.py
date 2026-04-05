import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.interval_tree import Interval, IntervalTree


# ──────────────────────────────────────────────
# pass_to_pass: these must always pass
# ──────────────────────────────────────────────


class TestIntervalBasics:
    """Tests for basic interval operations that already work correctly."""

    def test_insert_and_size(self):
        tree = IntervalTree()
        tree.insert(1, 5)
        tree.insert(6, 10)
        assert tree.size == 2

    def test_query_point_inside(self):
        tree = IntervalTree()
        tree.insert(1, 5)
        tree.insert(10, 20)
        results = tree.query(3)
        assert len(results) == 1
        assert results[0] == Interval(1, 5)

    def test_merge_fully_overlapping(self):
        """Merging intervals where one is fully contained in another."""
        tree = IntervalTree()
        tree.insert(1, 10)
        tree.insert(3, 7)
        merged = tree.merge_overlapping()
        assert len(merged) == 1
        assert merged[0] == Interval(1, 10)


# ──────────────────────────────────────────────
# fail_to_pass: these fail before the fix
# ──────────────────────────────────────────────


class TestMergeTouchingIntervals:
    """Tests for merging touching intervals — boundary overlap cases."""

    @pytest.mark.fail_to_pass
    def test_merge_touching_pair(self):
        """[1,3] and [3,5] share point 3 and must merge into [1,5]."""
        tree = IntervalTree()
        tree.insert(1, 3)
        tree.insert(3, 5)
        merged = tree.merge_overlapping()
        assert len(merged) == 1
        assert merged[0] == Interval(1, 5)

    @pytest.mark.fail_to_pass
    def test_merge_chain_of_touching(self):
        """A chain of touching intervals should collapse into one."""
        tree = IntervalTree()
        tree.insert(1, 5)
        tree.insert(5, 10)
        tree.insert(10, 15)
        merged = tree.merge_overlapping()
        assert len(merged) == 1
        assert merged[0] == Interval(1, 15)

    @pytest.mark.fail_to_pass
    def test_overlap_method_touching(self):
        """The overlaps() method itself should return True for touching intervals."""
        a = Interval(1, 3)
        b = Interval(3, 5)
        assert a.overlaps(b) is True
        assert b.overlaps(a) is True
