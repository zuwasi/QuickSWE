# SIMD Matrix Operations – Incorrect Alignment and Mask Handling

## Problem

A matrix library provides optimized 4×4 matrix operations (multiply, transpose,
determinant) using manual loop unrolling and cache-line-aware access patterns
(simulated without actual SIMD intrinsics for portability).

The implementation processes elements in blocks of 4 and uses a "mask" to handle
the tail when dimensions are not multiples of 4.

Users report:

1. Multiplying two 4×4 matrices produces wrong results because the accumulation
   loop has an off-by-one in the block stride.
2. The tail-handling mask incorrectly zeroes valid elements when the dimension
   is an exact multiple of 4.
3. The determinant computation for 4×4 matrices is wrong due to incorrect
   cofactor sign pattern.

## Files

- `src/simd_matrix.hpp` — matrix operations with block processing
- `src/main.cpp` — test driver
