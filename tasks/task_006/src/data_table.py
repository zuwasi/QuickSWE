class DataTable:
    """A simple in-memory data table that stores rows as list of dicts."""

    def __init__(self):
        self._rows = []

    def add_row(self, row):
        """Add a row (dict) to the table."""
        if not isinstance(row, dict):
            raise TypeError("Row must be a dictionary")
        self._rows.append(dict(row))

    def get_rows(self):
        """Return all rows as a list of dicts."""
        return [dict(r) for r in self._rows]

    def filter_by(self, column, value):
        """Return rows where column equals value."""
        return [dict(r) for r in self._rows if r.get(column) == value]
