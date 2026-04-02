# Task 022: Add Query Builder with Joins to ORM

## Current State

We have a mini ORM with:

- `src/model.py` — `Model` base class with field declarations and a `table_name` class attribute
- `src/query.py` — `QueryBuilder` that supports `select()`, `where()`, `order_by()` and generates SQL strings
- `src/connection.py` — `MockConnection` that records all executed queries for testing

The query builder works fine for single-table queries. You can do things like:

```python
q = QueryBuilder(User)
q.select("name", "email").where("active = 1").order_by("name")
q.build()  # → "SELECT name, email FROM users WHERE active = 1 ORDER BY name"
```

## Feature Request

We need JOIN support. In practice we keep having to write raw SQL for anything involving two tables, which defeats the purpose of having a query builder.

We need:
- `query.join(OtherModel, on="field")` — produces `JOIN other_table ON main_table.field = other_table.field`
- `query.left_join(OtherModel, on="field")` — same but `LEFT JOIN`
- When joins are present, `select()` should accept `"table.column"` syntax and the generated SQL should use table-prefixed column names
- Multiple joins should be chainable

Don't overthink the ON clause — matching on a single field name that exists in both tables is fine for now. But if someone passes `on="users.id = orders.user_id"` (a full condition), just use it as-is.

## Constraints

- Existing single-table queries must continue to work without any changes
- `build()` should return the full SQL string
- `MockConnection.execute(query_builder)` should store the built SQL in its history

## Acceptance Criteria

- [ ] `query.join(Model, on=...)` generates correct INNER JOIN SQL
- [ ] `query.left_join(Model, on=...)` generates correct LEFT JOIN SQL
- [ ] Select with table prefixes works across joined tables
- [ ] Multiple joins can be chained
- [ ] Existing select/where/order_by queries unchanged
