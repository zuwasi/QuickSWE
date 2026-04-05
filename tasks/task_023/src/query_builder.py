"""
SQL query builder with a fluent API for constructing SELECT statements.

Supports JOINs, WHERE clauses, ORDER BY, GROUP BY, HAVING, and LIMIT.
All output is parameterized to prevent SQL injection.
"""

from typing import List, Tuple, Optional, Any, Dict


class Condition:
    """Represents a WHERE or HAVING condition."""

    def __init__(self, clause: str, params: Optional[List[Any]] = None):
        self.clause = clause
        self.params = params or []

    def __str__(self):
        return self.clause


class JoinClause:
    """Represents a JOIN in the query."""

    def __init__(self, join_type: str, table: str, left_col: str,
                 right_col: str, alias: Optional[str] = None):
        self.join_type = join_type
        self.table = table
        self.left_col = left_col
        self.right_col = right_col
        self.alias = alias or table

    def to_sql(self) -> str:
        table_ref = f"{self.table} AS {self.alias}" if self.alias != self.table else self.table
        return f"{self.join_type} JOIN {table_ref} ON {self.left_col} = {self.right_col}"


class QueryBuilder:
    """Fluent SQL query builder."""

    def __init__(self):
        self._select_columns: List[str] = []
        self._from_table: Optional[str] = None
        self._from_alias: Optional[str] = None
        self._joins: List[JoinClause] = []
        self._where: List[Condition] = []
        self._group_by: List[str] = []
        self._having: List[Condition] = []
        self._order_by: List[Tuple[str, str]] = []
        self._limit: Optional[int] = None
        self._offset: Optional[int] = None
        self._distinct: bool = False
        self._params: List[Any] = []

    def select(self, *columns: str) -> "QueryBuilder":
        self._select_columns.extend(columns)
        return self

    def distinct(self) -> "QueryBuilder":
        self._distinct = True
        return self

    def from_table(self, table: str, alias: Optional[str] = None) -> "QueryBuilder":
        self._from_table = table
        self._from_alias = alias or table
        return self

    def join(self, table: str, left_col: str, right_col: str,
             join_type: str = "INNER", alias: Optional[str] = None) -> "QueryBuilder":
        resolved_alias = alias or table
        if len(self._joins) == 0:
            resolved_left = f"{self._from_alias}.{left_col}"
        else:
            last_join = self._joins[-1]
            resolved_left = f"{last_join.alias}.{left_col}"
        resolved_right = f"{resolved_alias}.{right_col}"
        self._joins.append(JoinClause(
            join_type=join_type,
            table=table,
            left_col=resolved_left,
            right_col=resolved_right,
            alias=resolved_alias,
        ))
        return self

    def left_join(self, table: str, left_col: str, right_col: str,
                  alias: Optional[str] = None) -> "QueryBuilder":
        return self.join(table, left_col, right_col, "LEFT", alias)

    def right_join(self, table: str, left_col: str, right_col: str,
                   alias: Optional[str] = None) -> "QueryBuilder":
        return self.join(table, left_col, right_col, "RIGHT", alias)

    def where(self, clause: str, *params: Any) -> "QueryBuilder":
        self._where.append(Condition(clause, list(params)))
        return self

    def where_in(self, column: str, values: List[Any]) -> "QueryBuilder":
        placeholders = ", ".join(["?"] * len(values))
        self._where.append(Condition(f"{column} IN ({placeholders})", list(values)))
        return self

    def where_between(self, column: str, low: Any, high: Any) -> "QueryBuilder":
        self._where.append(Condition(f"{column} BETWEEN ? AND ?", [low, high]))
        return self

    def group_by(self, *columns: str) -> "QueryBuilder":
        self._group_by.extend(columns)
        return self

    def having(self, clause: str, *params: Any) -> "QueryBuilder":
        self._having.append(Condition(clause, list(params)))
        return self

    def order_by(self, column: str, direction: str = "ASC") -> "QueryBuilder":
        self._order_by.append((column, direction.upper()))
        return self

    def limit(self, count: int) -> "QueryBuilder":
        self._limit = count
        return self

    def offset(self, count: int) -> "QueryBuilder":
        self._offset = count
        return self

    def build(self) -> Tuple[str, List[Any]]:
        if not self._from_table:
            raise ValueError("FROM table is required")
        if not self._select_columns:
            self._select_columns = ["*"]

        parts = []
        params = []

        select_keyword = "SELECT DISTINCT" if self._distinct else "SELECT"
        parts.append(f"{select_keyword} {', '.join(self._select_columns)}")

        from_ref = f"{self._from_table} AS {self._from_alias}" if self._from_alias != self._from_table else self._from_table
        parts.append(f"FROM {from_ref}")

        for j in self._joins:
            parts.append(j.to_sql())

        if self._where:
            where_clauses = [str(w) for w in self._where]
            parts.append(f"WHERE {' AND '.join(where_clauses)}")
            for w in self._where:
                params.extend(w.params)

        if self._group_by:
            parts.append(f"GROUP BY {', '.join(self._group_by)}")

        if self._having:
            having_clauses = [str(h) for h in self._having]
            parts.append(f"HAVING {' AND '.join(having_clauses)}")
            for h in self._having:
                params.extend(h.params)

        if self._order_by:
            order_parts = [f"{col} {dir}" for col, dir in self._order_by]
            parts.append(f"ORDER BY {', '.join(order_parts)}")

        if self._limit is not None:
            parts.append(f"LIMIT {self._limit}")

        if self._offset is not None:
            parts.append(f"OFFSET {self._offset}")

        return " ".join(parts), params

    def to_sql(self) -> str:
        sql, _ = self.build()
        return sql


class SubqueryBuilder:
    """Allows building subqueries that can be used in FROM or WHERE clauses."""

    def __init__(self, builder: QueryBuilder, alias: str):
        self.builder = builder
        self.alias = alias

    def to_sql(self) -> str:
        inner_sql, _ = self.builder.build()
        return f"({inner_sql}) AS {self.alias}"


def build_insert(table: str, data: Dict[str, Any]) -> Tuple[str, List[Any]]:
    columns = list(data.keys())
    placeholders = ", ".join(["?"] * len(columns))
    sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
    return sql, list(data.values())


def build_update(table: str, data: Dict[str, Any],
                 where: str, where_params: List[Any]) -> Tuple[str, List[Any]]:
    set_parts = [f"{col} = ?" for col in data.keys()]
    sql = f"UPDATE {table} SET {', '.join(set_parts)} WHERE {where}"
    return sql, list(data.values()) + where_params


def build_delete(table: str, where: str,
                 where_params: List[Any]) -> Tuple[str, List[Any]]:
    sql = f"DELETE FROM {table} WHERE {where}"
    return sql, where_params
