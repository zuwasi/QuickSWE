import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.query_builder import QueryBuilder, build_insert, build_update


class TestQueryBuilderPassToPass:
    """Tests that should pass both before and after the fix."""

    def test_simple_select(self):
        qb = QueryBuilder()
        sql = qb.select("id", "name").from_table("users").to_sql()
        assert "SELECT id, name" in sql
        assert "FROM users" in sql

    def test_single_join(self):
        qb = QueryBuilder()
        sql = (qb.select("*")
               .from_table("orders")
               .join("customers", "customer_id", "id")
               .to_sql())
        assert "JOIN customers ON orders.customer_id = customers.id" in sql

    def test_where_clause(self):
        qb = QueryBuilder()
        sql, params = (qb.select("*")
                       .from_table("users")
                       .where("age > ?", 18)
                       .build())
        assert "WHERE age > ?" in sql
        assert params == [18]


@pytest.mark.fail_to_pass
class TestQueryBuilderFailToPass:
    """Tests that fail before the fix and pass after."""

    def test_three_table_join_references_correct_tables(self):
        qb = QueryBuilder()
        sql = (qb.select("*")
               .from_table("orders")
               .join("customers", "customer_id", "id")
               .join("products", "product_id", "id")
               .to_sql())
        assert "orders.customer_id = customers.id" in sql
        assert "orders.product_id = products.id" in sql

    def test_four_table_join(self):
        qb = QueryBuilder()
        sql = (qb.select("*")
               .from_table("orders", "o")
               .join("customers", "customer_id", "id", alias="c")
               .join("products", "product_id", "id", alias="p")
               .join("categories", "category_id", "id", alias="cat")
               .to_sql())
        assert "o.customer_id = c.id" in sql
        assert "o.product_id = p.id" in sql
        assert "o.category_id = cat.id" in sql

    def test_mixed_join_types_correct_table_refs(self):
        qb = QueryBuilder()
        sql = (qb.select("*")
               .from_table("employees")
               .join("departments", "dept_id", "id")
               .left_join("managers", "manager_id", "id")
               .to_sql())
        assert "employees.dept_id = departments.id" in sql
        assert "employees.manager_id = managers.id" in sql

    def test_join_with_where_and_group(self):
        qb = QueryBuilder()
        sql, params = (qb.select("d.name", "COUNT(*)")
                       .from_table("employees", "e")
                       .join("departments", "dept_id", "id", alias="d")
                       .join("locations", "location_id", "id", alias="l")
                       .where("l.country = ?", "US")
                       .group_by("d.name")
                       .build())
        assert "e.dept_id = d.id" in sql
        assert "e.location_id = l.id" in sql
        assert params == ["US"]
