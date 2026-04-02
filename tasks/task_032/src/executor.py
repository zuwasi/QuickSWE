"""Query executor — runs parsed queries against registered tables.

TODO: Implement query execution:
1. Resolve table from registry
2. Apply JOIN if present
3. Apply WHERE filters
4. Apply GROUP BY + aggregate computation
5. Apply HAVING filters
6. Apply ORDER BY
7. Apply SELECT projection (column selection + aliases)
"""

from .table import Table
from .query_parser import QueryParser, ParsedQuery


class QueryExecutor:
    """Executes parsed queries against in-memory tables."""

    def __init__(self):
        self._parser = QueryParser()

    def execute(self, query_string):
        """Parse and execute a query string.

        Args:
            query_string: SQL-like query string.

        Returns:
            List of dicts (result rows).
        """
        # TODO: Implement full query execution pipeline
        raise NotImplementedError("QueryExecutor.execute() is not yet implemented")

    def execute_parsed(self, parsed):
        """Execute a pre-parsed query.

        Args:
            parsed: ParsedQuery object.

        Returns:
            List of dicts (result rows).
        """
        # TODO: Implement
        raise NotImplementedError("QueryExecutor.execute_parsed() is not yet implemented")
