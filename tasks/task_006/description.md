# Feature Request: Add Sorting to DataTable

## Current State

The `DataTable` class in `src/data_table.py` supports:
- `add_row(row_dict)` — adds a row (dict) to the table
- `get_rows()` — returns all rows as a list of dicts
- `filter_by(column, value)` — returns rows where `column == value`

## Requested Feature

Add a `sort_by(column, reverse=False)` method that returns the rows sorted by the given column's values.

- `column` (str): the column name to sort by
- `reverse` (bool, default False): if True, sort in descending order
- Returns a new list of the rows sorted by that column (does NOT mutate internal state)
- If a row is missing the specified column, it should be placed at the end of the sorted result

## Acceptance Criteria

1. `sort_by("age")` returns rows sorted by the "age" column in ascending order
2. `sort_by("age", reverse=True)` returns rows sorted descending
3. Rows missing the sort column are placed at the end
4. The internal row order is not mutated by sorting
5. All existing functionality (add_row, get_rows, filter_by) continues to work
