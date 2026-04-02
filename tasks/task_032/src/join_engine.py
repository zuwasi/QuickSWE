"""Join engine — performs inner joins between two tables.

TODO: Implement inner join logic.
Given two sets of rows and a join condition (left_col = right_col),
produce the cross-product filtered by matching column values.
Column names should be prefixed with table name to avoid ambiguity:
e.g., "orders.customer_id" and "customers.id".
"""


class JoinEngine:
    """Performs join operations between tables."""

    def inner_join(self, left_rows, right_rows, left_col, right_col,
                   left_table_name="left", right_table_name="right"):
        """Perform an inner join.

        Args:
            left_rows: List of dicts from the left table.
            right_rows: List of dicts from the right table.
            left_col: Column name in left table to join on.
            right_col: Column name in right table to join on.
            left_table_name: Name prefix for left table columns.
            right_table_name: Name prefix for right table columns.

        Returns:
            List of dicts with combined columns (prefixed with table names).
        """
        # TODO: Implement inner join
        raise NotImplementedError("JoinEngine.inner_join() is not yet implemented")
