import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.btree import BTree


class TestBTreePassToPass:
    """Tests that should pass both before and after the fix."""

    def test_insert_and_search_small(self):
        bt = BTree(t=2)
        bt.insert(10)
        bt.insert(20)
        bt.insert(5)
        assert bt.contains(10)
        assert bt.contains(20)
        assert bt.contains(5)
        assert not bt.contains(99)

    def test_minimum_and_maximum(self):
        bt = BTree(t=2)
        for v in [30, 10, 50, 20, 40]:
            bt.insert(v)
        assert bt.minimum() == 10
        assert bt.maximum() == 50

    def test_inorder_sorted_small(self):
        bt = BTree(t=2)
        for v in [3, 1, 2]:
            bt.insert(v)
        assert bt.inorder() == [1, 2, 3]


@pytest.mark.fail_to_pass
class TestBTreeFailToPass:
    """Tests that fail before the fix and pass after."""

    def test_no_duplicate_keys_after_splits(self):
        bt = BTree(t=2)
        for v in range(1, 11):
            bt.insert(v)
        result = bt.inorder()
        assert len(result) == len(set(result)), f"Duplicates found: {result}"
        assert result == list(range(1, 11))

    def test_count_keys_matches_inserted(self):
        bt = BTree(t=3)
        values = [15, 5, 25, 10, 20, 30, 1, 3, 7, 12, 17, 22, 27, 35]
        for v in values:
            bt.insert(v)
        assert bt.count_keys() == len(values)

    def test_valid_tree_after_many_inserts(self):
        bt = BTree(t=2)
        for v in range(1, 21):
            bt.insert(v)
        assert bt.is_valid(), "B-tree invariants violated after inserts"

    def test_search_all_keys_after_split(self):
        bt = BTree(t=2)
        values = list(range(1, 16))
        for v in values:
            bt.insert(v)
        for v in values:
            assert bt.contains(v), f"Key {v} not found after insertion"
