import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.spiral import spiral_order


# ──────────────────────────────────────────────
# pass_to_pass: these must always pass
# ──────────────────────────────────────────────


class TestSpiralBasics:
    """Tests for spiral traversal cases that already work."""

    def test_empty_matrix(self):
        assert spiral_order([]) == []
        assert spiral_order([[]]) == []

    def test_single_element(self):
        assert spiral_order([[42]]) == [42]

    def test_single_row(self):
        assert spiral_order([[1, 2, 3, 4]]) == [1, 2, 3, 4]


# ──────────────────────────────────────────────
# fail_to_pass: these fail before the fix
# ──────────────────────────────────────────────


class TestSpiralRectangular:
    """Tests for rectangular (non-square) matrices that expose the bug."""

    @pytest.mark.fail_to_pass
    def test_3x4_matrix(self):
        matrix = [
            [1, 2, 3, 4],
            [5, 6, 7, 8],
            [9, 10, 11, 12],
        ]
        expected = [1, 2, 3, 4, 8, 12, 11, 10, 9, 5, 6, 7]
        result = spiral_order(matrix)
        assert result == expected, f"Expected {expected}, got {result}"

    @pytest.mark.fail_to_pass
    def test_4x3_matrix(self):
        matrix = [
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 9],
            [10, 11, 12],
        ]
        expected = [1, 2, 3, 6, 9, 12, 11, 10, 7, 4, 5, 8]
        result = spiral_order(matrix)
        assert result == expected, f"Expected {expected}, got {result}"

    @pytest.mark.fail_to_pass
    def test_3x5_matrix(self):
        matrix = [
            [1, 2, 3, 4, 5],
            [6, 7, 8, 9, 10],
            [11, 12, 13, 14, 15],
        ]
        expected = [1, 2, 3, 4, 5, 10, 15, 14, 13, 12, 11, 6, 7, 8, 9]
        result = spiral_order(matrix)
        assert result == expected, f"Expected {expected}, got {result}"
