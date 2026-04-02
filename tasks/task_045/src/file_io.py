"""File I/O utilities for ETL — CSV-like parsing from string data."""


def parse_csv_data(raw_data: str) -> list[dict]:
    """Parse CSV-formatted string data into a list of dictionaries.

    First line is treated as header. Subsequent lines are data rows.
    Empty lines are skipped.

    Args:
        raw_data: Multi-line CSV string.

    Returns:
        List of dicts, one per data row, keyed by header names.
    """
    lines = [line.strip() for line in raw_data.strip().split("\n") if line.strip()]
    if not lines:
        return []
    headers = [h.strip() for h in lines[0].split(",")]
    records = []
    for line in lines[1:]:
        values = [v.strip() for v in line.split(",")]
        if len(values) != len(headers):
            continue  # skip malformed rows
        record = dict(zip(headers, values))
        records.append(record)
    return records


def read_source(source: str) -> list[dict]:
    """Read and parse source data.

    Args:
        source: CSV-formatted string (simulates file reading).

    Returns:
        List of parsed records.
    """
    return parse_csv_data(source)
