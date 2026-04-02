# Task 014: Convert Callback-Based Code to Use Exceptions

## Current State

`src/processor.py` contains a `DataProcessor` class whose methods all return `(success: bool, result_or_error)` tuples. Callers must check the boolean on every call:

```python
ok, result = processor.parse_json(raw)
if not ok:
    print(f"Error: {result}")
    return
ok, cleaned = processor.clean_data(result)
if not ok:
    print(f"Error: {cleaned}")
    return
```

This pattern is extremely verbose, obscures the happy path, and makes chaining difficult.

## Code Smell

- **Error code instead of exceptions** — Go-style tuple returns in Python, defeating EAFP.
- Every method returns `(True, value)` on success or `(False, "error message")` on failure.

## Requested Refactoring

1. Define two custom exception classes at module level:
   - `ProcessingError(Exception)` — for general processing failures.
   - `ValidationError(Exception)` — for input validation failures.
2. Change each method to **return the result directly** on success and **raise** `ProcessingError` or `ValidationError` on failure.
3. The success-path return values must match the second element of the current `(True, ...)` tuples.

## Acceptance Criteria

- [ ] `ProcessingError` and `ValidationError` are importable from `src.processor`.
- [ ] `parse_json(valid_json)` returns the parsed dict directly (not a tuple).
- [ ] `parse_json(bad_json)` raises `ProcessingError`.
- [ ] `validate_record(invalid_record)` raises `ValidationError`.
- [ ] All methods that currently succeed still return the same values.
