# Bug Report: WMMA Tensor Core GEMM Produces Wrong Results

## Summary

Our WMMA-based matrix multiplication kernel using tensor cores produces
incorrect results. The fragment loading uses the wrong layout specifier,
causing the matrix data to be interpreted with wrong row/column ordering.

## Symptoms

- Output matrix doesn't match CPU reference `C = A * B`.
- Matrix A is stored in row-major but loaded with `col_major` layout.
- Matrix B is stored in row-major but loaded with `col_major` layout.
- The leading dimension parameter passed to `load_matrix_sync` uses
  the wrong dimension (N instead of K for matrix A).
- Small matrices (16x16) show transposed-looking errors.

## Expected Behavior

- C = A * B should match CPU reference for any M, N, K dimensions.
- Fragment layouts must match actual memory layout.

## Build Notes

Compile with: `nvcc -rdc=true -lcudadevrt -lm -arch=sm_70` (or higher)
