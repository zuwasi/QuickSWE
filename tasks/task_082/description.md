# Bug Report: CSR SpMV Gives Wrong Results for Last Row and Empty Rows

## Summary

Our CUDA sparse matrix-vector multiplication (CSR format) kernel produces
wrong results. The last row always has an incorrect value and empty rows
produce non-zero garbage instead of zero.

## Symptoms

- The last row of the result vector is always wrong.
- The kernel special-cases the last row using `nnz` instead of
  `row_ptr[row+1]`, but this is incorrect when the last row doesn't
  extend to the last non-zero.
- Empty rows (where `row_ptr[i] == row_ptr[i+1]`) produce garbage
  because the sum accumulator starts with an uninitialized value
  instead of 0.
- Interior rows with non-zero entries appear correct sometimes.

## Expected Behavior

- `y[i] = sum(val[j] * x[col[j]])` for `j` in `row_ptr[i]..row_ptr[i+1]-1`.
- Empty rows should produce `y[i] = 0`.
- Last row should be handled identically to other rows.

## Build Notes

Compile with: `nvcc -rdc=true -lcudadevrt -lm`
