import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.jsonpath import JSONPathEvaluator, tokenize_path


# ──────────────────────────────────────────────
# pass_to_pass: these must always pass
# ──────────────────────────────────────────────


class TestJSONPathBasics:
    """Tests for basic path access that already works."""

    def test_simple_key_access(self):
        data = {"name": "Alice", "age": 30}
        ev = JSONPathEvaluator(data)
        assert ev.query("$.name") == ["Alice"]

    def test_nested_key_access(self):
        data = {"user": {"profile": {"email": "a@b.com"}}}
        ev = JSONPathEvaluator(data)
        assert ev.query("$.user.profile.email") == ["a@b.com"]

    def test_array_index_access(self):
        data = {"items": [10, 20, 30]}
        ev = JSONPathEvaluator(data)
        assert ev.query("$.items[0]") == [10]
        assert ev.query("$.items[2]") == [30]


# ──────────────────────────────────────────────
# fail_to_pass: these fail before the fix
# ──────────────────────────────────────────────


class TestArrayWildcard:
    """Tests for [*] wildcard — should return all array elements."""

    @pytest.mark.fail_to_pass
    def test_wildcard_returns_all_elements(self):
        data = {"colors": ["red", "green", "blue"]}
        ev = JSONPathEvaluator(data)
        result = ev.query("$.colors[*]")
        assert result == ["red", "green", "blue"]

    @pytest.mark.fail_to_pass
    def test_wildcard_with_nested_key(self):
        data = {
            "books": [
                {"title": "A", "year": 2020},
                {"title": "B", "year": 2021},
                {"title": "C", "year": 2022},
            ]
        }
        ev = JSONPathEvaluator(data)
        result = ev.query("$.books[*].title")
        assert result == ["A", "B", "C"]

    @pytest.mark.fail_to_pass
    def test_wildcard_on_nested_arrays(self):
        data = {"matrix": {"rows": [1, 2, 3, 4, 5]}}
        ev = JSONPathEvaluator(data)
        result = ev.query("$.matrix.rows[*]")
        assert result == [1, 2, 3, 4, 5]

    @pytest.mark.fail_to_pass
    def test_wildcard_exists_check(self):
        data = {"items": [1, 2]}
        ev = JSONPathEvaluator(data)
        assert ev.exists("$.items[*]") is True
