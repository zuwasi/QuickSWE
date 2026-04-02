# Feature Request: Add JSON Export to Report Generator

## Current State

The `ReportGenerator` class in `src/report.py` supports:
- `__init__(self, title, data)` — takes a report title (str) and data (list of dicts)
- `generate_text()` — returns a formatted text report string with title header and rows

## Requested Feature

Add two new methods:

### `generate_json()`
Returns a JSON string representation of the report with the structure:
```json
{
    "title": "Report Title",
    "generated_at": "ISO-format timestamp",
    "record_count": 3,
    "data": [...]
}
```

### `export(format, filepath)`
Writes the report to a file in the specified format.
- `format` (str): either `"text"` or `"json"`
- `filepath` (str): path to write the file
- Raises `ValueError` for unsupported formats

## Acceptance Criteria

1. `generate_json()` returns valid JSON with title, generated_at, record_count, and data fields
2. `export("text", path)` writes the text report to the file
3. `export("json", path)` writes the JSON report to the file
4. `export("xml", path)` raises ValueError
5. Existing `generate_text()` continues to work unchanged
