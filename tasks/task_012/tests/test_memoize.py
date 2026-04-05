import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.memoize import memoize, MemoizedProperty


# ─── fail_to_pass ───────────────────────────────────────────────

@pytest.mark.fail_to_pass
def test_mutable_list_arg_returns_correct_result():
    """Two different list objects with the same content must hit cache."""
    @memoize
    def process(items):
        return sum(items)

    list_a = [1, 2, 3]
    list_b = [1, 2, 3]
    assert list_a is not list_b

    result1 = process(list_a)
    result2 = process(list_b)
    assert result1 == 6
    assert result2 == 6
    assert process.cache_info()["hits"] == 1, (
        f"Expected 1 cache hit for equal lists, got {process.cache_info()}"
    )


@pytest.mark.fail_to_pass
def test_mutated_list_gives_fresh_result():
    """After mutating a list, calling again must return a new result."""
    @memoize
    def total(items):
        return sum(items)

    data = [1, 2, 3]
    r1 = total(data)
    assert r1 == 6

    data.append(4)
    r2 = total(data)
    assert r2 == 10, f"Expected 10 after mutation, got {r2}"


@pytest.mark.fail_to_pass
def test_dict_kwarg_caching():
    """Dict keyword args with same content must be treated equally."""
    @memoize
    def lookup(mapping, key):
        return mapping.get(key, None)

    d1 = {"a": 1, "b": 2}
    d2 = {"a": 1, "b": 2}
    r1 = lookup(d1, "a")
    r2 = lookup(d2, "a")
    assert r1 == r2 == 1
    assert lookup.cache_info()["hits"] == 1


# ─── pass_to_pass ───────────────────────────────────────────────

def test_basic_immutable_caching():
    """Simple int arguments cache correctly."""
    call_count = 0

    @memoize
    def add(a, b):
        nonlocal call_count
        call_count += 1
        return a + b

    assert add(2, 3) == 5
    assert add(2, 3) == 5
    assert call_count == 1


def test_cache_clear():
    """cache_clear resets everything."""
    @memoize
    def square(x):
        return x * x

    square(4)
    square.cache_clear()
    info = square.cache_info()
    assert info["hits"] == 0
    assert info["misses"] == 0
    assert info["size"] == 0


def test_memoized_property():
    """MemoizedProperty caches per instance."""
    class Rect:
        def __init__(self, w, h):
            self.w = w
            self.h = h

        @MemoizedProperty
        def area(self):
            return self.w * self.h

    r = Rect(3, 4)
    assert r.area == 12
    assert r.area == 12
