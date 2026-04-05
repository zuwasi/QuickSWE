# Task 023: SQL Query Builder Multi-Table JOIN Bug

## Problem

A SQL query builder generates incorrect JOIN ON clauses when more than two tables
are joined. The third and subsequent JOINs reference the wrong table alias in
the ON clause, producing semantically incorrect SQL.

## Expected Behavior

Each JOIN should reference the correct left-hand table in its ON clause:
```sql
SELECT ... FROM orders
  JOIN customers ON orders.customer_id = customers.id
  JOIN products ON orders.product_id = products.id
```

But instead the builder produces:
```sql
SELECT ... FROM orders
  JOIN customers ON orders.customer_id = customers.id
  JOIN products ON customers.product_id = products.id  -- WRONG: uses 'customers' instead of 'orders'
```

## Files

- `src/query_builder.py` — SQL query builder with fluent API
