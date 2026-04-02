"""Aggregate functions — COUNT, SUM, AVG, MIN, MAX.

TODO: Implement aggregate function classes.
Each should accept a list of values and return the aggregate result.
COUNT(*) counts all rows, COUNT(col) counts non-None values.
"""


class AggregateFunction:
    """Base class for aggregate functions."""

    def __init__(self, column=None):
        self._column = column

    @property
    def column(self):
        return self._column

    def compute(self, values):
        """Compute the aggregate over a list of values.

        Args:
            values: List of values from the grouped rows.

        Returns:
            The aggregate result.
        """
        raise NotImplementedError


class Count(AggregateFunction):
    """COUNT(*) or COUNT(column)."""

    def compute(self, values):
        # TODO: Implement
        raise NotImplementedError


class Sum(AggregateFunction):
    """SUM(column)."""

    def compute(self, values):
        # TODO: Implement
        raise NotImplementedError


class Avg(AggregateFunction):
    """AVG(column)."""

    def compute(self, values):
        # TODO: Implement
        raise NotImplementedError


class Min(AggregateFunction):
    """MIN(column)."""

    def compute(self, values):
        # TODO: Implement
        raise NotImplementedError


class Max(AggregateFunction):
    """MAX(column)."""

    def compute(self, values):
        # TODO: Implement
        raise NotImplementedError
