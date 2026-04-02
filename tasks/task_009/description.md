# Feature Request: Add Search and Total Value to Inventory System

## Current State

The `Inventory` class in `src/inventory.py` supports:
- `add_item(name, quantity, price)` — adds an item to inventory
- `remove_item(name)` — removes an item by exact name
- `get_item(name)` — returns item dict by exact name, or None if not found

## Requested Feature

### `search(query)`
Case-insensitive partial name matching. Returns a list of item dicts whose name contains the query string (case-insensitive).

Example: `search("lap")` should find items named "Laptop", "LAPTOP", "laptop case", etc.

### `get_total_value()`
Returns the total inventory value: the sum of `quantity * price` for all items.

## Acceptance Criteria

1. `search("lap")` finds "Laptop" (case-insensitive partial match)
2. `search("LAP")` also finds "Laptop"
3. `search("xyz")` returns empty list when nothing matches
4. `search("")` returns all items (empty string matches everything)
5. `get_total_value()` returns correct sum of quantity * price
6. `get_total_value()` returns 0 for empty inventory
7. All existing functionality (add_item, remove_item, get_item) continues to work
