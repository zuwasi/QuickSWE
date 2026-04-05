# Task 007: Rotated Sorted Array Search

## Problem

The `search(nums, target)` function performs binary search on a rotated sorted array. A rotated sorted array is a sorted array that has been rotated at some pivot (e.g., `[4,5,6,7,0,1,2]`).

The function works for many cases but **fails to find elements that sit at the left boundary of a sorted half**. For example, searching for `4` in `[4,5,6,7,0,1,2]` returns `-1` instead of `0`, and searching for `1` in an unrotated `[1,2,3,4,5,6,7]` also fails.

## Expected Behavior

- `search([4,5,6,7,0,1,2], 4)` → `0`
- `search([1,2,3,4,5,6,7], 1)` → `0`
- `search([5,6,7,8,1,2,3,4], 1)` → `4`
- `search([4,5,6,7,0,1,2], 5)` → `1` (already works)
- Returns `-1` when target is not found

## Files

- `src/rotated_search.py` — Rotated array search implementation
- `tests/test_rotated_search.py` — Test suite
