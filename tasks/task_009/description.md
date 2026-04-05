# Task 009: Markdown Table Parser — Escaped Pipes

## Problem

The `parse_table(text)` function parses a Markdown-formatted table into a list of dictionaries (one per row, keyed by header names). It currently splits cells on the `|` character, but **doesn't handle escaped pipes `\|`** within cell content.

When a cell contains a literal pipe character (written as `\|` in Markdown), it should be treated as part of the cell content rather than a column separator.

## Expected Behavior

- `| A \| B | C |` should parse as two cells: `"A | B"` and `"C"`
- Unescaped pipes remain column delimiters
- The separator row (e.g., `|---|---|`) should still be recognized
- Normal tables without escaped pipes should continue to work

## Files

- `src/markdown_table.py` — Markdown table parser
- `tests/test_markdown_table.py` — Test suite
