import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.data_table import DataTable


# ──────────────────────────────────────────────
# Pass-to-pass: existing functionality tests
# ──────────────────────────────────────────────

class TestExistingFunctionality:
    def setup_method(self):
        self.dt = DataTable()
        self.dt.add_row({"name": "Alice", "age": 30})
        self.dt.add_row({"name": "Bob", "age": 25})
        self.dt.add_row({"name": "Charlie", "age": 35})

    def test_add_row_and_get_rows(self):
        rows = self.dt.get_rows()
        assert len(rows) == 3
        assert rows[0]["name"] == "Alice"
        assert rows[1]["name"] == "Bob"
        assert rows[2]["name"] == "Charlie"

    def test_add_row_type_error(self):
        with pytest.raises(TypeError):
            self.dt.add_row("not a dict")

    def test_get_rows_returns_copies(self):
        rows = self.dt.get_rows()
        rows[0]["name"] = "Modified"
        assert self.dt.get_rows()[0]["name"] == "Alice"

    def test_filter_by_existing_value(self):
        result = self.dt.filter_by("name", "Bob")
        assert len(result) == 1
        assert result[0]["age"] == 25

    def test_filter_by_no_match(self):
        result = self.dt.filter_by("name", "Dave")
        assert len(result) == 0

    def test_filter_by_multiple_matches(self):
        self.dt.add_row({"name": "Alice", "age": 40})
        result = self.dt.filter_by("name", "Alice")
        assert len(result) == 2

    def test_empty_table(self):
        empty = DataTable()
        assert empty.get_rows() == []
        assert empty.filter_by("x", 1) == []


# ──────────────────────────────────────────────
# Fail-to-pass: sort_by feature tests
# ──────────────────────────────────────────────

class TestSortBy:
    def setup_method(self):
        self.dt = DataTable()
        self.dt.add_row({"name": "Charlie", "age": 35})
        self.dt.add_row({"name": "Alice", "age": 30})
        self.dt.add_row({"name": "Bob", "age": 25})

    @pytest.mark.fail_to_pass
    def test_sort_by_ascending(self):
        result = self.dt.sort_by("age")
        assert [r["name"] for r in result] == ["Bob", "Alice", "Charlie"]

    @pytest.mark.fail_to_pass
    def test_sort_by_descending(self):
        result = self.dt.sort_by("age", reverse=True)
        assert [r["name"] for r in result] == ["Charlie", "Alice", "Bob"]

    @pytest.mark.fail_to_pass
    def test_sort_by_string_column(self):
        result = self.dt.sort_by("name")
        assert [r["name"] for r in result] == ["Alice", "Bob", "Charlie"]

    @pytest.mark.fail_to_pass
    def test_sort_by_does_not_mutate(self):
        original_order = [r["name"] for r in self.dt.get_rows()]
        self.dt.sort_by("age")
        after_sort_order = [r["name"] for r in self.dt.get_rows()]
        assert original_order == after_sort_order

    @pytest.mark.fail_to_pass
    def test_sort_by_missing_column_at_end(self):
        self.dt.add_row({"name": "Dave"})  # no "age" key
        result = self.dt.sort_by("age")
        names = [r["name"] for r in result]
        assert names[-1] == "Dave"
        assert names[:3] == ["Bob", "Alice", "Charlie"]
