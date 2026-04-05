# Bug Report: 1D Convolution Incorrect at Boundaries

## Summary

Our tiled CUDA 1D convolution kernel produces incorrect results near
array boundaries. Interior elements are computed correctly, but elements
within `radius` of the start and end of the array are wrong.

## Symptoms

- Elements near index 0 and index N-1 have wrong values.
- The boundary (halo) loading logic reads out-of-bounds indices
  instead of clamping or zero-padding them.
- The halo offset calculation is wrong — left halo cells are loaded
  from `blockIdx.x * blockDim.x - radius` but with an incorrect
  index mapping, accessing wrong data or out-of-bounds memory.
- Elements in the middle of the array are correct.

## Expected Behavior

- Convolution should handle boundaries with zero-padding (elements
  outside the array are treated as 0.0).
- All N output elements should match the CPU reference.

## Build Notes

Compile with: `nvcc -rdc=true -lcudadevrt -lm`
