# Bug Report: Bitonic Sort Wrong for Non-Power-of-2 Arrays

## Summary

Our CUDA bitonic sort produces correctly sorted output for power-of-2
array sizes but scrambles results for any other size. The compare-and-swap
direction logic and the padding strategy both have issues.

## Symptoms

- Arrays of size 256, 512, 1024 sort correctly.
- Arrays of size 100, 300, 1000 produce garbled or partially sorted output.
- The padded values (FLT_MAX) leak into the first N positions.
- The ascending/descending direction bit uses the wrong bit position
  when determining swap direction, causing sub-sequences to sort in
  the wrong direction for the final merge stages.

## Expected Behavior

- First N elements of output should be sorted in ascending order.
- Should work for any array size by padding to next power-of-2.

## Build Notes

Compile with: `nvcc -rdc=true -lcudadevrt -lm`
