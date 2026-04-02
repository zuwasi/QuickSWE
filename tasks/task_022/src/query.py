"""Query builder for generating SQL strings."""


class QueryBuilder:
    """Builds SQL SELECT queries for a given model."""

    def __init__(self, model_class):
        self._model = model_class
        self._table = model_class.table_name
        self._columns = []
        self._where_clauses = []
        self._order_columns = []

    def select(self, *columns):
        """Specify columns to select. If empty, selects all."""
        self._columns.extend(columns)
        return self

    def where(self, condition: str):
        """Add a WHERE condition (raw SQL string)."""
        self._where_clauses.append(condition)
        return self

    def order_by(self, column: str, direction: str = "ASC"):
        """Add an ORDER BY clause."""
        self._order_columns.append(f"{column} {direction}")
        return self

    def build(self) -> str:
        """Build and return the SQL query string."""
        # SELECT
        if self._columns:
            cols = ", ".join(self._columns)
        else:
            cols = "*"
        sql = f"SELECT {cols} FROM {self._table}"

        # WHERE
        if self._where_clauses:
            where = " AND ".join(self._where_clauses)
            sql += f" WHERE {where}"

        # ORDER BY
        if self._order_columns:
            order = ", ".join(self._order_columns)
            sql += f" ORDER BY {order}"

        return sql

    def __repr__(self):
        return f"QueryBuilder({self._table}): {self.build()}"
