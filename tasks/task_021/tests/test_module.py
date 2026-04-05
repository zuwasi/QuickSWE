import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.rbtree import RBTree


class TestRBTreePassToPass:
    """Tests that should pass both before and after the fix."""

    def test_insert_and_search(self):
        tree = RBTree()
        for v in [10, 20, 30, 15, 25]:
            tree.insert(v)
        assert tree.search(10) is not None
        assert tree.search(20) is not None
        assert tree.search(99) is None

    def test_inorder_after_inserts(self):
        tree = RBTree()
        values = [50, 30, 70, 20, 40, 60, 80]
        for v in values:
            tree.insert(v)
        assert tree.inorder() == sorted(values)

    def test_simple_delete_leaf(self):
        tree = RBTree()
        for v in [10, 5, 15]:
            tree.insert(v)
        tree.delete(5)
        assert tree.search(5) is None
        assert tree.search(10) is not None
        assert tree.search(15) is not None


@pytest.mark.fail_to_pass
class TestRBTreeFailToPass:
    """Tests that fail before the fix and pass after."""

    def test_delete_odd_elements_preserves_rb(self):
        tree = RBTree()
        for v in range(1, 16):
            tree.insert(v)
        for d in [1, 3, 5, 7, 9]:
            tree.delete(d)
        assert tree.is_valid_rb_tree()

    def test_delete_even_elements_preserves_rb(self):
        tree = RBTree()
        for v in range(1, 16):
            tree.insert(v)
        for d in [2, 4, 6, 8, 10]:
            tree.delete(d)
        assert tree.is_valid_rb_tree()

    def test_delete_middle_range_preserves_rb(self):
        tree = RBTree()
        for v in range(1, 16):
            tree.insert(v)
        for d in [10, 9, 8, 7, 6]:
            tree.delete(d)
        assert tree.is_valid_rb_tree()

    def test_black_height_consistent_after_deletions(self):
        tree = RBTree()
        for v in range(1, 21):
            tree.insert(v)
        for d in [5, 10, 15, 20, 3, 7, 13, 17]:
            tree.delete(d)
        bh = tree.black_height()
        assert bh > 0

    def test_delete_alternating_preserves_properties(self):
        tree = RBTree()
        values = list(range(1, 31))
        for v in values:
            tree.insert(v)
        for v in values[::2]:
            tree.delete(v)
        assert tree.is_valid_rb_tree()
        assert tree.black_height() > 0
