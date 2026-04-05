# Bug Report: Matrix Transpose Produces Incorrect Results

## Summary

Our tiled CUDA matrix transpose kernel produces incorrect output for
non-square matrices and even for some square matrices. The transposed
matrix has elements in wrong positions.

## Symptoms

- Square matrices (e.g., 32x32) produce partially correct results but
  some elements are swapped within tiles.
- Non-square matrices (e.g., 64x48) produce completely garbled output.
- The shared memory tile read indices appear swapped, causing elements
  to end up in wrong output positions.
- Output coordinate calculation for the transposed write doesn't
  correctly account for the tile position swap.

## Expected Behavior

- `out[j][i] = in[i][j]` for all valid indices.
- Should work for any matrix dimensions, not just multiples of tile size.

## Build Notes

Compile with: `nvcc -rdc=true -lcudadevrt -lm`
