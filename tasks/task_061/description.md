# Bug: Matrix Multiplication with Wrong Indexing

## Description

A matrix multiplication function computes C = A × B. The inner loop accumulates the dot product but writes to the wrong index: `C[i][k] += A[i][k] * B[k][j]` instead of `C[i][j] += A[i][k] * B[k][j]`.

This bug is sneaky because it produces correct results for square identity-like tests where the indices happen to align, but produces garbage for non-square matrices or general rectangular matrix multiplication.

## Expected Behavior

For A (2×3) and B (3×2), the result C (2×2) should be the correct matrix product.

## Actual Behavior

The result C has wrong values because each inner-loop iteration overwrites `C[i][k]` instead of accumulating into `C[i][j]`.

## Files

- `src/matrix.h` — struct and function declarations
- `src/matrix.c` — matrix multiplication implementation with the bug
- `src/main.c` — test driver
