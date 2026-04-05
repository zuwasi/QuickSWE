import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.rotated_search import search


# ──────────────────────────────────────────────
# pass_to_pass: these must always pass
# ──────────────────────────────────────────────


class TestRotatedSearchBasics:
    """Tests for rotated search cases that already work."""

    def test_target_found_in_rotated(self):
        assert search([4, 5, 6, 7, 0, 1, 2], 5) == 1

    def test_target_not_found(self):
        assert search([4, 5, 6, 7, 0, 1, 2], 3) == -1

    def test_empty_array(self):
        assert search([], 5) == -1

    def test_single_element_found(self):
        assert search([1], 1) == 0


# ──────────────────────────────────────────────
# fail_to_pass: these fail before the fix
# ──────────────────────────────────────────────


class TestRotatedSearchEdgeCases:
    """Tests that fail when left-boundary element is excluded from range check."""

    @pytest.mark.fail_to_pass
    def test_find_leftmost_in_sorted_half(self):
        """When target equals nums[left], the sorted-half check must include it."""
        nums = [4, 5, 6, 7, 0, 1, 2]
        assert search(nums, 4) == 0

    @pytest.mark.fail_to_pass
    def test_unrotated_array_find_first(self):
        """Unrotated array: finding the first element fails with strict <."""
        nums = [1, 2, 3, 4, 5, 6, 7]
        assert search(nums, 1) == 0

    @pytest.mark.fail_to_pass
    def test_find_rotation_point_element(self):
        """Finding the minimum element (start of the right sorted half)."""
        nums = [5, 6, 7, 8, 1, 2, 3, 4]
        assert search(nums, 1) == 4
