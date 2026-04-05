# Task 001: Interval Tree Merge Overlapping

## Problem

The `IntervalTree` class provides functionality to store intervals and merge overlapping ones. However, the `merge_overlapping()` method fails to merge intervals that are "touching" — i.e., where one interval's end equals another interval's start (e.g., `[1, 3]` and `[3, 5]` should merge into `[1, 5]`).

In standard interval arithmetic, touching intervals (where one ends exactly where another begins) are considered overlapping and should be merged.

## Expected Behavior

- `merge_overlapping()` on intervals `[1, 3]` and `[3, 5]` should produce `[1, 5]`
- `merge_overlapping()` on intervals `[1, 5]`, `[5, 10]`, `[10, 15]` should produce `[1, 15]`
- Non-touching intervals like `[1, 3]` and `[4, 6]` should remain separate

## Files

- `src/interval_tree.py` — IntervalTree implementation with insert, query, and merge_overlapping
- `tests/test_interval_tree.py` — Test suite
