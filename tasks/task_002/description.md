# Bug: CSV parser crashes on empty input and mismatched row lengths

## Description

The `parse_csv(text)` function parses CSV-formatted text into a list of dictionaries. It has two bugs:

1. **Empty input:** Crashes with `IndexError` on empty string input because it unconditionally accesses `lines[0]` for the header row even when there are no lines.
2. **Mismatched field counts:** Raises `ValueError` when a data row has more or fewer fields than the header (e.g. trailing commas or missing values). It should gracefully handle these by truncating extra fields or padding missing ones with empty strings.

## Expected Behavior

- `parse_csv("")` should return an empty list `[]`.
- Rows with trailing commas (extra fields) should be truncated to header count.
- Rows with fewer fields than headers should pad missing values with `""`.

## Actual Behavior

- `parse_csv("")` raises `IndexError: list index out of range`.
- `parse_csv("name,age\nAlice,30,")` raises `ValueError: Row has 3 fields, expected 2`.
- `parse_csv("name,age,city\nAlice,30")` raises `ValueError: Row has 2 fields, expected 3`.

## How to Reproduce

```python
from csv_parser import parse_csv

parse_csv("")                          # IndexError
parse_csv("name,age\nAlice,30,")       # ValueError
parse_csv("name,age,city\nAlice,30")   # ValueError
```
