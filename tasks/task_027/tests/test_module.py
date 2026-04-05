import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.ast_rename import VariableRenamer, ScopeAnalyzer, find_all_references


class TestASTRenamePassToPass:
    """Tests that should pass both before and after the fix."""

    def test_simple_rename(self):
        source = '''
def foo(x):
    return x + 1
'''
        renamer = VariableRenamer("foo", "x", "value")
        result = renamer.rename(source)
        assert "value" in result
        assert "x" not in result.split("def foo(")[1]

    def test_rename_in_assignment(self):
        source = '''
def calc(a, b):
    result = a + b
    return result
'''
        renamer = VariableRenamer("calc", "result", "total")
        result = renamer.rename(source)
        assert "total" in result

    def test_no_rename_outside_target(self):
        source = '''
def foo(x):
    return x

def bar(x):
    return x * 2
'''
        renamer = VariableRenamer("foo", "x", "y")
        result = renamer.rename(source)
        assert "def bar(x)" in result


@pytest.mark.fail_to_pass
class TestASTRenameFailToPass:
    """Tests that fail before the fix and pass after."""

    def test_nested_function_shadow_not_renamed(self):
        source = '''
def outer(x):
    y = x + 1
    def inner(x):
        return x * 2
    return inner(y)
'''
        renamer = VariableRenamer("outer", "x", "value")
        result = renamer.rename(source)
        assert "def inner(x)" in result
        assert "return x * 2" in result
        assert "value" in result.split("def outer")[1].split("def inner")[0]

    def test_deeply_nested_shadow_preserved(self):
        source = '''
def outer(val):
    a = val + 1
    def middle():
        val = 99
        def inner():
            return val
        return inner()
    return a + middle()
'''
        renamer = VariableRenamer("outer", "val", "input_val")
        result = renamer.rename(source)
        lines = result.strip().split("\n")
        outer_part = result.split("def middle")[0]
        assert "input_val" in outer_part
        middle_part = result.split("def middle")[1]
        assert "val = 99" in middle_part
        assert "return val" in middle_part

    def test_nested_param_shadow_not_renamed(self):
        source = '''
def calculate(x, y):
    total = x + y
    def helper(x):
        return x * 2
    return total + helper(10)
'''
        renamer = VariableRenamer("calculate", "x", "first")
        result = renamer.rename(source)
        assert "def helper(x)" in result
        assert "return x * 2" in result
        assert "def calculate(first" in result
