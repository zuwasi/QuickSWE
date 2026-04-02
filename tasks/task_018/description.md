# Bug Report: Task scheduler rejects valid diamond dependencies and silently allows cycles

## Summary

We have a task scheduler that resolves execution order using a dependency graph. Tasks declare their dependencies, and the scheduler resolves the correct order using topological sort. There's also a `validate()` method and `has_cycle()` check.

## Problem

Two separate issues have been reported:

1. **False positive cycle detection**: The `has_cycle()` method (and `validate()`) incorrectly reports cycles in dependency graphs that have "diamond" patterns — where two tasks share a common dependency. For example: `setup` is needed by both `build_frontend` and `build_backend`, and `deploy` needs both of them. This is a perfectly valid DAG, but `has_cycle()` says it's circular.

2. **Missing cycle detection in resolve_order**: When there IS a real circular dependency (A depends on B, B depends on C, C depends on A), `resolve_order()` doesn't raise any error — it silently produces some ordering without detecting the cycle. This leads to undefined behavior at runtime.

## Steps to Reproduce

For issue 1:
1. Create a diamond dependency: A→B→D and A→C→D
2. Call `has_cycle()` — it returns `True` (WRONG)

For issue 2:
1. Create circular deps: A→B→C→A
2. Call `resolve_order()` — no error raised (should raise `ValueError`)

## Expected Behavior

- Diamond dependencies should be recognized as valid (no cycle)
- Actual cycles should be detected and raise a clear `ValueError`
- `resolve_order()` should validate the graph before sorting

## Environment

- Python 3.10+
- Custom dependency resolution (no external libraries)
