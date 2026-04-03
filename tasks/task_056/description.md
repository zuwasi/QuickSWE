# Bug Report: Incorrect CUDA Grid Dimensions for Non-Power-of-2 Arrays

## Summary

The `vector_add` CUDA kernel produces incorrect results for arrays whose size
is not evenly divisible by the block size (e.g., N=1000 with BLOCK_SIZE=256).
The last portion of the array contains uninitialized or stale values instead of
the expected sum.

## Steps to Reproduce

1. Compile `src/vector_add.cu` with `nvcc`.
2. Run the resulting binary with `--size 1000`.
3. Observe that elements beyond index 767 are incorrect (typically zero or
   garbage values instead of the correct vector sum).

## Expected Behavior

All 1000 elements of the output array should contain the correct sum of the
corresponding elements from vectors A and B.

For `a[i] = i` and `b[i] = i * 2`, the expected result is `c[i] = i + i*2 = 3*i`
for every `i` in `[0, 999]`.

## Actual Behavior

Elements at indices 768–999 are **not computed** by the kernel. The output for
those indices is zero (as initialized by `cudaMemset` / `cudaMalloc` behavior)
instead of the expected values.

## Root Cause Analysis

There are **two bugs** in `vector_add.cu`:

1. **Grid dimension truncation**: The grid size is computed as:
   ```c
   int grid = N / BLOCK_SIZE;
   ```
   For N=1000 and BLOCK_SIZE=256, this yields `grid = 3` (integer division
   truncates). Only `3 * 256 = 768` threads are launched, leaving elements
   768–999 unprocessed. The fix is to round up:
   ```c
   int grid = (N + BLOCK_SIZE - 1) / BLOCK_SIZE;
   ```

2. **Missing bounds check in kernel**: Once the grid is rounded up (grid=4,
   launching 1024 threads), threads with index >= N will perform out-of-bounds
   memory accesses. The kernel must include:
   ```c
   if (i < N) { ... }
   ```

Both bugs must be fixed together. Fixing only the grid dimension without adding
the bounds check causes undefined behavior. Fixing only the bounds check
without the grid rounding still leaves trailing elements unprocessed.

## Environment

- CUDA Toolkit 12.x
- Windows 11 / Linux
- Any NVIDIA GPU with compute capability >= 3.5
