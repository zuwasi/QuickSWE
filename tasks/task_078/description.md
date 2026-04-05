# Bug Report: GPU Histogram Counts Are Wrong

## Summary

Our CUDA histogram kernel produces incorrect bin counts. The totals are
always lower than the CPU reference, and the error grows with larger
input arrays.

## Symptoms

- Small arrays (~100 elements) sometimes produce correct results.
- Larger arrays (10000+) always have incorrect counts.
- Total count across all bins is less than N (some increments are lost).
- The histogram uses direct global memory increments without atomicAdd,
  causing race conditions when multiple threads update the same bin.

## Expected Behavior

- Each bin count should exactly match the CPU reference histogram.
- Total across all bins should equal N.

## Build Notes

Compile with: `nvcc -rdc=true -lcudadevrt -lm`
