import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.segment_tree import SegmentTree


class TestSegmentTreePassToPass:
    """Tests that should pass both before and after the fix."""

    def test_build_and_full_query(self):
        st = SegmentTree([1, 2, 3, 4, 5])
        assert st.range_query(0, 4) == 15

    def test_point_update(self):
        st = SegmentTree([1, 2, 3, 4, 5])
        st.point_update(2, 10)
        assert st.range_query(0, 4) == 22

    def test_range_update_full_range(self):
        st = SegmentTree([0, 0, 0, 0])
        st.range_update(0, 3, 5)
        assert st.range_query(0, 3) == 20


@pytest.mark.fail_to_pass
class TestSegmentTreeFailToPass:
    """Tests that fail before the fix and pass after."""

    def test_point_query_after_range_update(self):
        """Query a single element within a range-updated segment."""
        st = SegmentTree([1] * 8)
        st.range_update(2, 5, 10)
        assert st.range_query(2, 2) == 11

    def test_partial_overlap_query(self):
        """Query partially overlaps a lazy-updated node."""
        st = SegmentTree([1, 1, 1, 1, 1, 1, 1, 1])
        st.range_update(2, 5, 10)
        assert st.range_query(3, 4) == 22

    def test_multiple_updates_then_point_query(self):
        """Multiple overlapping updates, then query a single element."""
        st = SegmentTree([0] * 8)
        st.range_update(0, 7, 1)
        st.range_update(2, 5, 3)
        assert st.range_query(3, 3) == 4

    def test_update_query_update_query_sequence(self):
        """Interleaved updates and queries."""
        st = SegmentTree([1, 1, 1, 1])
        st.range_update(0, 3, 1)
        assert st.range_query(0, 1) == 4
        st.range_update(1, 2, 5)
        assert st.range_query(1, 2) == 14
