"""
Markdown Table Parser.

Parses Markdown-formatted tables into Python data structures. Supports
standard Markdown table syntax with header rows, separator rows, and
data rows.

Example input:
    | Name  | Age |
    |-------|-----|
    | Alice | 30  |

Example output:
    [{"Name": "Alice", "Age": "30"}]
"""

import re


def _split_row(line):
    """Split a Markdown table row into cell values.

    Strips the leading and trailing pipes, then splits on pipe characters.
    Each cell value is stripped of surrounding whitespace.

    Args:
        line: A single line of a Markdown table.

    Returns:
        List of cell value strings.
    """
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]

    cells = stripped.split("|")
    return [cell.strip() for cell in cells]


def _is_separator_row(cells):
    """Check if a list of cell values represents a separator row.

    Separator rows contain only dashes, colons, and spaces.

    Args:
        cells: List of cell value strings.

    Returns:
        True if this is a separator row.
    """
    for cell in cells:
        cleaned = cell.replace("-", "").replace(":", "").replace(" ", "")
        if cleaned:
            return False
    return True


def parse_table(text):
    """Parse a Markdown table into a list of dictionaries.

    Each dictionary represents a row, with keys from the header row.
    The separator row is detected and skipped automatically.

    Args:
        text: A string containing a Markdown table.

    Returns:
        A list of dicts, one per data row.

    Raises:
        ValueError: If the table has no header or no data rows.
    """
    lines = [line for line in text.strip().split("\n") if line.strip()]

    if len(lines) < 2:
        raise ValueError("Table must have at least a header and separator row")

    headers = _split_row(lines[0])

    # Find and skip the separator row
    sep_index = None
    for i in range(1, len(lines)):
        cells = _split_row(lines[i])
        if _is_separator_row(cells):
            sep_index = i
            break

    if sep_index is None:
        raise ValueError("No separator row found in table")

    rows = []
    for line in lines[sep_index + 1:]:
        cells = _split_row(line)

        # Pad or truncate cells to match header count
        while len(cells) < len(headers):
            cells.append("")
        cells = cells[:len(headers)]

        row = dict(zip(headers, cells))
        rows.append(row)

    return rows


def table_to_markdown(headers, rows):
    """Convert headers and rows back into a Markdown table string.

    Args:
        headers: List of header strings.
        rows: List of dicts (one per row).

    Returns:
        A Markdown table string.
    """
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, h in enumerate(headers):
            val = str(row.get(h, ""))
            col_widths[i] = max(col_widths[i], len(val))

    def format_row(values):
        cells = [str(v).ljust(col_widths[i]) for i, v in enumerate(values)]
        return "| " + " | ".join(cells) + " |"

    result = [format_row(headers)]
    result.append("| " + " | ".join("-" * w for w in col_widths) + " |")
    for row in rows:
        values = [row.get(h, "") for h in headers]
        result.append(format_row(values))

    return "\n".join(result)


def get_column(table_data, column_name):
    """Extract all values from a named column.

    Args:
        table_data: List of dicts from parse_table().
        column_name: The header name to extract.

    Returns:
        List of values from that column.

    Raises:
        KeyError: If the column doesn't exist.
    """
    if not table_data:
        return []
    if column_name not in table_data[0]:
        raise KeyError(f"Column not found: {column_name}")
    return [row[column_name] for row in table_data]
