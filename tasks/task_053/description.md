# Matrix Multiplication – Incorrect Dimension Indexing

## Problem

A `Matrix` class supports dynamic-size matrix creation, element access, and
multiplication. Users report that matrix multiplication produces wrong results:

1. Multiplying non-square matrices (e.g., 2×3 * 3×2) gives incorrect values.
2. The identity matrix property `A * I = A` fails for rectangular matrices.
3. Transposing the product `(A*B)^T` does not equal `B^T * A^T`.

## Files

- `src/matrix.hpp` — Matrix class with multiply, transpose, and helpers
- `src/main.cpp` — test driver

## Expected Behaviour

- Standard matrix multiplication: `C[i][j] = sum(A[i][k] * B[k][j])` for k in
  0..A.cols-1, where result dimensions are A.rows × B.cols.
- The result matrix must have `A.rows` rows and `B.cols` columns.
