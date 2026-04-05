import os
import sys
import pytest
import threading
import ast
import inspect
import textwrap

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.concurrent_lru import ConcurrentLRU


class TestConcurrentLRUPassToPass:
    """Tests that should pass both before and after the fix."""

    def test_put_and_get(self):
        cache = ConcurrentLRU(3)
        cache.put("a", 1)
        assert cache.get("a") == 1

    def test_capacity_eviction(self):
        cache = ConcurrentLRU(2)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("c", 3)
        assert cache.get("a") is None
        assert cache.get("b") == 2
        assert cache.get("c") == 3

    def test_delete(self):
        cache = ConcurrentLRU(3)
        cache.put("x", 10)
        assert cache.delete("x")
        assert cache.get("x") is None


def _count_statements_outside_with(func) -> int:
    """Count how many statements in the function body are outside any `with` block."""
    source = textwrap.dedent(inspect.getsource(func))
    tree = ast.parse(source)
    func_def = tree.body[0]
    outside_count = 0
    for stmt in func_def.body:
        if isinstance(stmt, ast.With):
            continue
        if isinstance(stmt, (ast.Return, ast.Expr, ast.Assign)):
            outside_count += 1
    return outside_count


@pytest.mark.fail_to_pass
class TestConcurrentLRUFailToPass:
    """Tests that fail before the fix and pass after.

    The bug: get() releases the lock before calling move_to_end() and touch().
    These operations outside the lock cause race conditions.
    """

    def test_all_operations_under_lock(self):
        """In get(), move_to_end and touch must be inside the with-lock block,
        not after it. Count statements outside the with block."""
        outside = _count_statements_outside_with(ConcurrentLRU.get)
        assert outside == 0, (
            f"Found {outside} statements outside the lock in get(). "
            f"All cache operations must be atomic under the lock.")

    def test_touch_under_lock(self):
        """touch() must be called inside the with-lock block."""
        source = textwrap.dedent(inspect.getsource(ConcurrentLRU.get))
        tree = ast.parse(source)
        func_def = tree.body[0]

        touch_outside = False
        for stmt in func_def.body:
            if not isinstance(stmt, ast.With):
                for child in ast.walk(stmt):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Attribute) and child.func.attr == 'touch':
                            touch_outside = True

        assert not touch_outside, (
            "touch() is called outside the lock. It must be inside the with self._lock block.")

    def test_move_to_end_under_lock(self):
        """move_to_end must be inside the with-lock block."""
        source = textwrap.dedent(inspect.getsource(ConcurrentLRU.get))
        tree = ast.parse(source)
        func_def = tree.body[0]

        move_in_with = False
        for stmt in ast.walk(func_def):
            if isinstance(stmt, ast.With):
                for child in ast.walk(stmt):
                    if isinstance(child, ast.Attribute) and child.attr == 'move_to_end':
                        move_in_with = True
        top_level_has_move = False
        for stmt in func_def.body:
            if not isinstance(stmt, ast.With):
                for child in ast.walk(stmt):
                    if isinstance(child, ast.Attribute) and child.attr == 'move_to_end':
                        top_level_has_move = True

        assert move_in_with and not top_level_has_move, (
            "move_to_end must be called inside the with self._lock block, not outside it.")

    def test_return_value_under_lock(self):
        """The return of the value must be inside the with-lock block."""
        source = textwrap.dedent(inspect.getsource(ConcurrentLRU.get))
        tree = ast.parse(source)
        func_def = tree.body[0]

        returns_outside = 0
        for stmt in func_def.body:
            if not isinstance(stmt, ast.With):
                for child in ast.walk(stmt):
                    if isinstance(child, ast.Return) and child.value is not None:
                        if isinstance(child.value, ast.Name) and child.value.id == 'value':
                            returns_outside += 1
                        elif isinstance(child.value, ast.Attribute):
                            returns_outside += 1

        assert returns_outside == 0, (
            f"Found {returns_outside} return statements outside the lock. "
            f"The value return must be inside the with self._lock block.")
