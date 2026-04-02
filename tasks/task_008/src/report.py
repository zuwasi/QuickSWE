class ReportGenerator:
    """Generates formatted reports from tabular data."""

    def __init__(self, title, data):
        """
        Initialize the report generator.

        Args:
            title: Report title string.
            data: List of dicts representing rows of data.
        """
        self.title = title
        self.data = list(data)

    def generate_text(self):
        """Generate a plain text report."""
        lines = []
        lines.append("=" * 40)
        lines.append(self.title.center(40))
        lines.append("=" * 40)
        lines.append(f"Records: {len(self.data)}")
        lines.append("-" * 40)

        for i, row in enumerate(self.data, 1):
            lines.append(f"Record {i}:")
            for key, value in row.items():
                lines.append(f"  {key}: {value}")
            lines.append("")

        lines.append("=" * 40)
        return "\n".join(lines)
