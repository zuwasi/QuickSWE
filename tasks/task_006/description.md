# Task 006: Matrix Spiral Traversal

## Problem

The `spiral_order(matrix)` function traverses a 2D matrix in spiral order (right → down → left → up, repeating inward). It works correctly for square matrices but **skips inner elements for non-square (rectangular) matrices** due to an off-by-one error in the boundary update logic.

## Expected Behavior

- `spiral_order([[1,2,3],[4,5,6],[7,8,9]])` → `[1,2,3,6,9,8,7,4,5]`
- `spiral_order([[1,2,3,4],[5,6,7,8],[9,10,11,12]])` → `[1,2,3,4,8,12,11,10,9,5,6,7]`
- Single row and single column matrices should also work
- Empty matrix returns empty list

## Files

- `src/spiral.py` — spiral_order implementation
- `tests/test_spiral.py` — Test suite
