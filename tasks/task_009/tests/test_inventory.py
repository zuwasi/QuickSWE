import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.inventory import Inventory


# ──────────────────────────────────────────────
# Pass-to-pass: existing functionality tests
# ──────────────────────────────────────────────

class TestExistingFunctionality:
    def setup_method(self):
        self.inv = Inventory()
        self.inv.add_item("Laptop", 10, 999.99)
        self.inv.add_item("Mouse", 50, 29.99)
        self.inv.add_item("Keyboard", 30, 79.99)

    def test_add_and_get_item(self):
        item = self.inv.get_item("Laptop")
        assert item is not None
        assert item["name"] == "Laptop"
        assert item["quantity"] == 10
        assert item["price"] == 999.99

    def test_get_item_returns_copy(self):
        item = self.inv.get_item("Laptop")
        item["quantity"] = 999
        assert self.inv.get_item("Laptop")["quantity"] == 10

    def test_get_item_not_found(self):
        assert self.inv.get_item("Tablet") is None

    def test_remove_item(self):
        self.inv.remove_item("Mouse")
        assert self.inv.get_item("Mouse") is None

    def test_remove_item_not_found(self):
        with pytest.raises(KeyError):
            self.inv.remove_item("Tablet")

    def test_add_overwrites_existing(self):
        self.inv.add_item("Laptop", 20, 1099.99)
        item = self.inv.get_item("Laptop")
        assert item["quantity"] == 20
        assert item["price"] == 1099.99

    def test_empty_inventory(self):
        inv = Inventory()
        assert inv.get_item("anything") is None


# ──────────────────────────────────────────────
# Fail-to-pass: search and total value tests
# ──────────────────────────────────────────────

class TestSearch:
    def setup_method(self):
        self.inv = Inventory()
        self.inv.add_item("Laptop", 10, 999.99)
        self.inv.add_item("Laptop Case", 25, 49.99)
        self.inv.add_item("Mouse", 50, 29.99)
        self.inv.add_item("Keyboard", 30, 79.99)

    @pytest.mark.fail_to_pass
    def test_search_partial_match(self):
        results = self.inv.search("lap")
        names = [r["name"] for r in results]
        assert "Laptop" in names
        assert "Laptop Case" in names
        assert len(results) == 2

    @pytest.mark.fail_to_pass
    def test_search_case_insensitive(self):
        results = self.inv.search("LAP")
        names = [r["name"] for r in results]
        assert "Laptop" in names

    @pytest.mark.fail_to_pass
    def test_search_no_match(self):
        results = self.inv.search("xyz")
        assert results == []

    @pytest.mark.fail_to_pass
    def test_search_empty_query_returns_all(self):
        results = self.inv.search("")
        assert len(results) == 4

    @pytest.mark.fail_to_pass
    def test_search_exact_match(self):
        results = self.inv.search("Mouse")
        assert len(results) == 1
        assert results[0]["name"] == "Mouse"


class TestTotalValue:
    @pytest.mark.fail_to_pass
    def test_get_total_value(self):
        inv = Inventory()
        inv.add_item("A", 10, 5.00)
        inv.add_item("B", 20, 2.50)
        # 10*5.00 + 20*2.50 = 50 + 50 = 100
        assert inv.get_total_value() == 100.0

    @pytest.mark.fail_to_pass
    def test_get_total_value_empty(self):
        inv = Inventory()
        assert inv.get_total_value() == 0

    @pytest.mark.fail_to_pass
    def test_get_total_value_single_item(self):
        inv = Inventory()
        inv.add_item("Widget", 3, 10.0)
        assert inv.get_total_value() == 30.0
