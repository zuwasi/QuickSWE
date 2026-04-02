"""Query parser — parses SQL-like query strings into a structured query object.

TODO: Implement parsing for:
- SELECT col1, col2 FROM table
- SELECT * FROM table
- SELECT col AS alias FROM table
- WHERE col op value  (op: =, !=, >, <, >=, <=)
- ORDER BY col ASC|DESC
- GROUP BY col
- HAVING aggregate_expr op value
- JOIN table2 ON t1.col = t2.col
- Aggregate functions: COUNT(*), SUM(col), AVG(col), MIN(col), MAX(col)
"""


class ParsedQuery:
    """Structured representation of a parsed query."""

    def __init__(self):
        self.select_columns = []  # List of (column_or_aggregate, alias_or_None)
        self.from_table = None
        self.where_conditions = []  # List of (column, operator, value)
        self.order_by = []  # List of (column, 'ASC'|'DESC')
        self.group_by = []  # List of column names
        self.having_conditions = []  # List of (aggregate_expr, operator, value)
        self.join = None  # (table_name, left_col, right_col) or None


class QueryParser:
    """Parses SQL-like query strings into ParsedQuery objects."""

    def parse(self, query_string):
        """Parse a query string into a ParsedQuery.

        Args:
            query_string: SQL-like query string.

        Returns:
            ParsedQuery object.

        Raises:
            SyntaxError: If the query is malformed.
        """
        # TODO: Implement query parsing
        raise NotImplementedError("QueryParser.parse() is not yet implemented")
