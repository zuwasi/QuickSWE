# Task 032: SQL-like Query Engine for In-Memory Data

## Overview

Implement a working in-memory query engine that supports a subset of SQL. Data is stored in `Table` objects (list of dicts). Queries are parsed from SQL-like strings and executed against registered tables.

## Requirements

1. **SELECT**: `SELECT col1, col2 FROM table_name` and `SELECT * FROM table_name`
2. **WHERE**: `SELECT * FROM t WHERE col > value`, supporting `=`, `!=`, `>`, `<`, `>=`, `<=`
3. **ORDER BY**: `SELECT * FROM t ORDER BY col ASC|DESC`
4. **GROUP BY + Aggregates**: `SELECT col, COUNT(*), SUM(col2) FROM t GROUP BY col`
5. **HAVING**: `SELECT col, COUNT(*) FROM t GROUP BY col HAVING COUNT(*) > 2`
6. **JOIN**: `SELECT * FROM t1 JOIN t2 ON t1.id = t2.fk` (inner join)
7. **Column aliases**: `SELECT col1 AS alias1 FROM t`
8. **Aggregate functions**: COUNT, SUM, AVG, MIN, MAX

## Existing Code

- `table.py` has a working `Table` class with `add_row()`, `get_rows()`, and a registry.
- Other files have stubs that need to be completed.

## Constraints

- Pure Python, no external dependencies (no sqlite3, no pandas).
- String values in WHERE can be quoted with single quotes: `WHERE name = 'Alice'`
- Numeric values are auto-detected (int or float).
