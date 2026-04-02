import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.model import User, Order, Department
from src.query import QueryBuilder
from src.connection import MockConnection


# ── pass-to-pass: existing query builder functionality ───────────────

class TestBasicSelect:
    def test_select_all(self):
        sql = QueryBuilder(User).build()
        assert sql == "SELECT * FROM users"

    def test_select_specific_columns(self):
        sql = QueryBuilder(User).select("name", "email").build()
        assert sql == "SELECT name, email FROM users"

    def test_select_single_column(self):
        sql = QueryBuilder(Order).select("product").build()
        assert sql == "SELECT product FROM orders"


class TestWhere:
    def test_single_where(self):
        sql = QueryBuilder(User).select("name").where("active = 1").build()
        assert sql == "SELECT name FROM users WHERE active = 1"

    def test_multiple_where(self):
        sql = (QueryBuilder(User)
               .select("name")
               .where("active = 1")
               .where("department_id = 3")
               .build())
        assert "active = 1 AND department_id = 3" in sql

    def test_where_with_string_condition(self):
        sql = QueryBuilder(Order).where("status = 'shipped'").build()
        assert "WHERE status = 'shipped'" in sql


class TestOrderBy:
    def test_order_by_default_asc(self):
        sql = QueryBuilder(User).select("name").order_by("name").build()
        assert sql == "SELECT name FROM users ORDER BY name ASC"

    def test_order_by_desc(self):
        sql = QueryBuilder(User).select("name").order_by("name", "DESC").build()
        assert "ORDER BY name DESC" in sql

    def test_multiple_order_by(self):
        sql = (QueryBuilder(User)
               .select("name", "email")
               .order_by("name")
               .order_by("email", "DESC")
               .build())
        assert "ORDER BY name ASC, email DESC" in sql


class TestChaining:
    def test_full_chain(self):
        sql = (QueryBuilder(User)
               .select("name", "email")
               .where("active = 1")
               .order_by("name")
               .build())
        assert sql == "SELECT name, email FROM users WHERE active = 1 ORDER BY name ASC"

    def test_chaining_returns_self(self):
        qb = QueryBuilder(User)
        assert qb.select("name") is qb
        assert qb.where("active = 1") is qb
        assert qb.order_by("name") is qb


class TestMockConnection:
    def test_execute_stores_query(self):
        conn = MockConnection()
        qb = QueryBuilder(User).select("name")
        conn.execute(qb)
        assert len(conn) == 1
        assert conn.last_query == "SELECT name FROM users"

    def test_history_accumulates(self):
        conn = MockConnection()
        conn.execute(QueryBuilder(User).select("name"))
        conn.execute(QueryBuilder(Order).select("product"))
        assert len(conn) == 2
        assert "users" in conn.history[0]
        assert "orders" in conn.history[1]

    def test_clear_history(self):
        conn = MockConnection()
        conn.execute(QueryBuilder(User))
        conn.clear()
        assert len(conn) == 0
        assert conn.last_query is None


# ── fail-to-pass: JOIN support ───────────────────────────────────────

class TestJoinBasic:
    @pytest.mark.fail_to_pass
    def test_inner_join(self):
        sql = (QueryBuilder(User)
               .join(Order, on="id")
               .build())
        assert "JOIN orders ON users.id = orders.id" in sql

    @pytest.mark.fail_to_pass
    def test_left_join(self):
        sql = (QueryBuilder(User)
               .left_join(Order, on="id")
               .build())
        assert "LEFT JOIN orders ON users.id = orders.id" in sql

    @pytest.mark.fail_to_pass
    def test_join_with_full_condition(self):
        """When on= contains '=', use it as-is."""
        sql = (QueryBuilder(User)
               .join(Order, on="users.id = orders.user_id")
               .build())
        assert "JOIN orders ON users.id = orders.user_id" in sql

    @pytest.mark.fail_to_pass
    def test_join_returns_self(self):
        qb = QueryBuilder(User)
        assert qb.join(Order, on="id") is qb


class TestJoinWithSelect:
    @pytest.mark.fail_to_pass
    def test_select_with_table_prefix(self):
        sql = (QueryBuilder(User)
               .select("users.name", "orders.product")
               .join(Order, on="users.id = orders.user_id")
               .build())
        assert "SELECT users.name, orders.product" in sql
        assert "FROM users" in sql
        assert "JOIN orders" in sql

    @pytest.mark.fail_to_pass
    def test_join_with_where_and_order(self):
        sql = (QueryBuilder(User)
               .select("users.name", "orders.amount")
               .join(Order, on="users.id = orders.user_id")
               .where("orders.status = 'shipped'")
               .order_by("orders.amount", "DESC")
               .build())
        assert "JOIN orders ON users.id = orders.user_id" in sql
        assert "WHERE orders.status = 'shipped'" in sql
        assert "ORDER BY orders.amount DESC" in sql


class TestMultipleJoins:
    @pytest.mark.fail_to_pass
    def test_chained_joins(self):
        sql = (QueryBuilder(User)
               .select("users.name", "orders.product", "departments.name")
               .join(Order, on="users.id = orders.user_id")
               .join(Department, on="users.department_id = departments.id")
               .build())
        assert "JOIN orders ON users.id = orders.user_id" in sql
        assert "JOIN departments ON users.department_id = departments.id" in sql
        assert "users.name" in sql
        assert "departments.name" in sql

    @pytest.mark.fail_to_pass
    def test_mixed_join_types(self):
        sql = (QueryBuilder(User)
               .join(Order, on="users.id = orders.user_id")
               .left_join(Department, on="users.department_id = departments.id")
               .build())
        # One is INNER JOIN (or just JOIN), the other is LEFT JOIN
        assert "JOIN orders" in sql
        assert "LEFT JOIN departments" in sql


class TestJoinWithConnection:
    @pytest.mark.fail_to_pass
    def test_connection_records_join_query(self):
        conn = MockConnection()
        qb = (QueryBuilder(User)
              .select("users.name", "orders.product")
              .join(Order, on="users.id = orders.user_id")
              .where("orders.amount > 100"))
        conn.execute(qb)
        assert "JOIN" in conn.last_query
        assert "orders.amount > 100" in conn.last_query
