# Bug Fix: CUDA Sparse Matrix-Vector Multiply (SpMV) — CSR Format

## Summary

The `spmv.cu` file implements a CUDA kernel for sparse matrix-vector multiply
(SpMV) using the Compressed Sparse Row (CSR) format. There are two bugs:

1. **Wrong last-row boundary**: The kernel computes the end pointer for the
   last row using `N` (the number of rows) instead of using `row_ptr[row+1]`.
   Specifically, the kernel has a special case `end = (row == num_rows-1) ? nnz : row_ptr[row+1]`
   but `nnz` is passed incorrectly (it's always the total number of
   non-zeros, but due to a bug in the host code, the wrong value is sent).
   The correct approach is to simply always use `row_ptr[row+1]` since the
   CSR row_ptr array has `num_rows+1` entries by definition.

2. **Empty rows not handled**: When `row_ptr[row] == row_ptr[row+1]` (empty
   row), the kernel doesn't initialise the output to zero for that row. The
   output buffer isn't zeroed before the kernel runs, so empty rows contain
   garbage values.

## Acceptance Criteria

- SpMV must produce correct results for:
  - A small 4×4 identity matrix × vector.
  - A random 100×100 sparse matrix (density ~10%).
  - A matrix with deliberately empty rows.
  - A 1000×1000 sparse matrix.
- GPU result must match CPU reference within relative error < 1e-5.

## Current Bugs

```c
// BUG 1: uses special-case nnz for last row instead of row_ptr[row+1]
int end = (row == num_rows - 1) ? nnz : row_ptr[row + 1];

// BUG 2: output not zeroed for empty rows — result contains garbage
```

## Environment

- CUDA Toolkit 12.x
- Windows 11 / Linux
- Any NVIDIA GPU with compute capability >= 3.5
