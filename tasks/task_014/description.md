# Task 014 – DI Container Circular Dependency Detection

## Problem
The `Container` class provides simple dependency injection. Services are
registered with a factory function that can request other services. When
service A depends on B and B depends on A, `resolve()` enters infinite
recursion instead of raising a clear `CircularDependencyError`.

## Expected Behaviour
- `resolve()` must detect circular dependency chains and raise
  `CircularDependencyError` with a message listing the cycle.
- Non-circular resolution must continue to work as before.

## Files
- `src/di_container.py` – the buggy container
- `tests/test_di_container.py` – test suite
