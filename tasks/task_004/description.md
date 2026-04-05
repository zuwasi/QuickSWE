# Task 004: JSON Path Array Wildcard Support

## Problem

The `JSONPathEvaluator` class supports basic JSON path expressions like `.key` and `[0]` (array index access), but it lacks support for the array wildcard `[*]` syntax. When `[*]` is used, the evaluator should return all elements of the current array node, but instead it returns an empty list.

## Expected Behavior

- `$.store.books[*].title` should return all book titles
- `$.items[*]` should return all items in the array
- `[*]` should work at any level of nesting
- When `[*]` is applied to a non-array value, it should return an empty list
- Existing `.key` and `[N]` paths should continue to work

## Files

- `src/jsonpath.py` — JSONPath evaluator implementation
- `tests/test_jsonpath.py` — Test suite
