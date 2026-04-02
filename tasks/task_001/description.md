# Bug: Off-by-one in Paginator.get_page()

## Description

The `Paginator` class provides a `get_page(n)` method documented as **1-indexed** (page 1 is the first page). However, the internal implementation uses 0-indexed math without adjusting for the 1-based API, causing every page request to return the *next* page's data instead.

## Expected Behavior

- `get_page(1)` should return the first `page_size` items.
- `get_page(total_pages)` should return the last remaining items.
- Pages are numbered starting from 1.

## Actual Behavior

- `get_page(1)` returns what should be page 2's data (items starting at index `page_size`).
- `get_page(total_pages)` raises an `IndexError` or returns an empty list because the offset overshoots the data.

## How to Reproduce

```python
from paginator import Paginator

p = Paginator([1, 2, 3, 4, 5], page_size=2)
print(p.get_page(1))  # Expected: [1, 2], Actual: [3, 4]
print(p.get_page(3))  # Expected: [5], Actual: [] (empty — off the end)
```
