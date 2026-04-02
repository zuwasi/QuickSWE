"""Tests for the SQL-like query engine."""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.table import Table
from src.query_parser import QueryParser
from src.executor import QueryExecutor
from src.aggregates import Count, Sum, Avg, Min, Max
from src.join_engine import JoinEngine


@pytest.fixture(autouse=True)
def clean_registry():
    """Clear the table registry before each test."""
    Table.clear_registry()
    yield
    Table.clear_registry()


def make_employees():
    t = Table("employees", ["id", "name", "dept", "salary", "age"])
    t.add_row({"id": 1, "name": "Alice",   "dept": "eng",   "salary": 90000, "age": 30})
    t.add_row({"id": 2, "name": "Bob",     "dept": "eng",   "salary": 85000, "age": 35})
    t.add_row({"id": 3, "name": "Charlie", "dept": "sales", "salary": 70000, "age": 28})
    t.add_row({"id": 4, "name": "Diana",   "dept": "sales", "salary": 75000, "age": 32})
    t.add_row({"id": 5, "name": "Eve",     "dept": "eng",   "salary": 95000, "age": 29})
    t.add_row({"id": 6, "name": "Frank",   "dept": "hr",    "salary": 65000, "age": 45})
    t.add_row({"id": 7, "name": "Grace",   "dept": "hr",    "salary": 68000, "age": 38})
    return t


def make_orders():
    t = Table("orders", ["order_id", "customer_id", "amount", "product"])
    t.add_row({"order_id": 101, "customer_id": 1, "amount": 250, "product": "Widget"})
    t.add_row({"order_id": 102, "customer_id": 2, "amount": 150, "product": "Gadget"})
    t.add_row({"order_id": 103, "customer_id": 1, "amount": 300, "product": "Widget"})
    t.add_row({"order_id": 104, "customer_id": 3, "amount": 450, "product": "Gizmo"})
    t.add_row({"order_id": 105, "customer_id": 2, "amount": 200, "product": "Widget"})
    return t


def make_customers():
    t = Table("customers", ["id", "name", "city"])
    t.add_row({"id": 1, "name": "Acme Corp", "city": "NYC"})
    t.add_row({"id": 2, "name": "Beta Inc",  "city": "LA"})
    t.add_row({"id": 3, "name": "Gamma LLC", "city": "NYC"})
    return t


# ============================================================
# PASS-TO-PASS: Basic Table functionality
# ============================================================

class TestTableBasic:
    def test_create_table(self):
        t = Table("test_table", ["a", "b"])
        assert t.name == "test_table"
        assert t.columns == ["a", "b"]

    def test_add_and_get_rows(self):
        t = Table("t1", ["x", "y"])
        t.add_row({"x": 1, "y": 2})
        t.add_row({"x": 3, "y": 4})
        rows = t.get_rows()
        assert len(rows) == 2
        assert rows[0] == {"x": 1, "y": 2}
        assert rows[1] == {"x": 3, "y": 4}

    def test_missing_column_raises(self):
        t = Table("t2", ["a", "b", "c"])
        with pytest.raises(ValueError):
            t.add_row({"a": 1, "b": 2})

    def test_registry_lookup(self):
        t = Table("lookup_test")
        assert Table.get_table("lookup_test") is t

    def test_registry_missing_raises(self):
        with pytest.raises(KeyError):
            Table.get_table("nonexistent")

    def test_len(self):
        t = Table("len_test")
        t.add_row({"a": 1})
        t.add_row({"a": 2})
        assert len(t) == 2

    def test_get_rows_returns_copy(self):
        t = Table("copy_test")
        t.add_row({"a": 1})
        rows = t.get_rows()
        rows[0]["a"] = 999
        assert t.get_rows()[0]["a"] == 1


# ============================================================
# FAIL-TO-PASS: Query engine functionality
# ============================================================

@pytest.mark.fail_to_pass
class TestBasicSelect:
    def test_select_all(self):
        make_employees()
        ex = QueryExecutor()
        result = ex.execute("SELECT * FROM employees")
        assert len(result) == 7

    def test_select_columns(self):
        make_employees()
        ex = QueryExecutor()
        result = ex.execute("SELECT name, salary FROM employees")
        assert len(result) == 7
        assert set(result[0].keys()) == {"name", "salary"}

    def test_select_with_alias(self):
        make_employees()
        ex = QueryExecutor()
        result = ex.execute("SELECT name AS employee_name, salary AS pay FROM employees")
        assert "employee_name" in result[0]
        assert "pay" in result[0]
        assert result[0]["employee_name"] == "Alice"


@pytest.mark.fail_to_pass
class TestWhere:
    def test_where_equals_number(self):
        make_employees()
        ex = QueryExecutor()
        result = ex.execute("SELECT * FROM employees WHERE id = 3")
        assert len(result) == 1
        assert result[0]["name"] == "Charlie"

    def test_where_equals_string(self):
        make_employees()
        ex = QueryExecutor()
        result = ex.execute("SELECT * FROM employees WHERE dept = 'eng'")
        assert len(result) == 3

    def test_where_greater_than(self):
        make_employees()
        ex = QueryExecutor()
        result = ex.execute("SELECT * FROM employees WHERE salary > 80000")
        assert len(result) == 3
        for r in result:
            assert r["salary"] > 80000

    def test_where_less_than(self):
        make_employees()
        ex = QueryExecutor()
        result = ex.execute("SELECT * FROM employees WHERE age < 30")
        assert len(result) == 2

    def test_where_not_equals(self):
        make_employees()
        ex = QueryExecutor()
        result = ex.execute("SELECT * FROM employees WHERE dept != 'eng'")
        assert len(result) == 4

    def test_where_greater_equals(self):
        make_employees()
        ex = QueryExecutor()
        result = ex.execute("SELECT * FROM employees WHERE salary >= 90000")
        assert len(result) == 2

    def test_where_less_equals(self):
        make_employees()
        ex = QueryExecutor()
        result = ex.execute("SELECT * FROM employees WHERE age <= 30")
        assert len(result) == 3


@pytest.mark.fail_to_pass
class TestOrderBy:
    def test_order_by_asc(self):
        make_employees()
        ex = QueryExecutor()
        result = ex.execute("SELECT * FROM employees ORDER BY salary ASC")
        salaries = [r["salary"] for r in result]
        assert salaries == sorted(salaries)

    def test_order_by_desc(self):
        make_employees()
        ex = QueryExecutor()
        result = ex.execute("SELECT * FROM employees ORDER BY age DESC")
        ages = [r["age"] for r in result]
        assert ages == sorted(ages, reverse=True)

    def test_order_by_default_asc(self):
        make_employees()
        ex = QueryExecutor()
        result = ex.execute("SELECT * FROM employees ORDER BY name")
        names = [r["name"] for r in result]
        assert names == sorted(names)


@pytest.mark.fail_to_pass
class TestGroupByAndAggregates:
    def test_group_by_count(self):
        make_employees()
        ex = QueryExecutor()
        result = ex.execute("SELECT dept, COUNT(*) FROM employees GROUP BY dept")
        dept_counts = {r["dept"]: r["COUNT(*)"] for r in result}
        assert dept_counts["eng"] == 3
        assert dept_counts["sales"] == 2
        assert dept_counts["hr"] == 2

    def test_group_by_sum(self):
        make_employees()
        ex = QueryExecutor()
        result = ex.execute("SELECT dept, SUM(salary) FROM employees GROUP BY dept")
        dept_sums = {r["dept"]: r["SUM(salary)"] for r in result}
        assert dept_sums["eng"] == 270000
        assert dept_sums["sales"] == 145000
        assert dept_sums["hr"] == 133000

    def test_group_by_avg(self):
        make_employees()
        ex = QueryExecutor()
        result = ex.execute("SELECT dept, AVG(salary) FROM employees GROUP BY dept")
        dept_avgs = {r["dept"]: r["AVG(salary)"] for r in result}
        assert dept_avgs["eng"] == 90000
        assert dept_avgs["hr"] == 66500

    def test_group_by_min_max(self):
        make_employees()
        ex = QueryExecutor()
        result = ex.execute("SELECT dept, MIN(salary), MAX(salary) FROM employees GROUP BY dept")
        eng = [r for r in result if r["dept"] == "eng"][0]
        assert eng["MIN(salary)"] == 85000
        assert eng["MAX(salary)"] == 95000


@pytest.mark.fail_to_pass
class TestHaving:
    def test_having_count(self):
        make_employees()
        ex = QueryExecutor()
        result = ex.execute(
            "SELECT dept, COUNT(*) FROM employees GROUP BY dept HAVING COUNT(*) > 2"
        )
        assert len(result) == 1
        assert result[0]["dept"] == "eng"

    def test_having_sum(self):
        make_employees()
        ex = QueryExecutor()
        result = ex.execute(
            "SELECT dept, SUM(salary) FROM employees GROUP BY dept HAVING SUM(salary) >= 145000"
        )
        depts = {r["dept"] for r in result}
        assert "eng" in depts
        assert "sales" in depts
        assert "hr" not in depts


@pytest.mark.fail_to_pass
class TestJoin:
    def test_inner_join(self):
        make_orders()
        make_customers()
        ex = QueryExecutor()
        result = ex.execute(
            "SELECT * FROM orders JOIN customers ON orders.customer_id = customers.id"
        )
        assert len(result) == 5  # All orders match a customer

    def test_join_column_access(self):
        make_orders()
        make_customers()
        ex = QueryExecutor()
        result = ex.execute(
            "SELECT orders.order_id, customers.name FROM orders JOIN customers ON orders.customer_id = customers.id"
        )
        assert len(result) == 5
        # Check first order is from Acme Corp
        acme_orders = [r for r in result if r.get("customers.name") == "Acme Corp"
                       or r.get("name") == "Acme Corp"]
        assert len(acme_orders) == 2

    def test_join_with_where(self):
        make_orders()
        make_customers()
        ex = QueryExecutor()
        result = ex.execute(
            "SELECT * FROM orders JOIN customers ON orders.customer_id = customers.id WHERE orders.amount > 200"
        )
        assert len(result) == 3
        for r in result:
            amt = r.get("orders.amount") or r.get("amount")
            assert amt > 200


@pytest.mark.fail_to_pass
class TestCombined:
    def test_where_and_order(self):
        make_employees()
        ex = QueryExecutor()
        result = ex.execute(
            "SELECT name, salary FROM employees WHERE dept = 'eng' ORDER BY salary DESC"
        )
        assert len(result) == 3
        assert result[0]["name"] == "Eve"
        assert result[0]["salary"] == 95000

    def test_group_having_order(self):
        make_orders()
        ex = QueryExecutor()
        result = ex.execute(
            "SELECT product, COUNT(*), SUM(amount) FROM orders GROUP BY product HAVING COUNT(*) >= 2 ORDER BY SUM(amount) DESC"
        )
        assert len(result) == 1  # Only Widget has >= 2 orders
        assert result[0]["product"] == "Widget"
        assert result[0]["SUM(amount)"] == 750
