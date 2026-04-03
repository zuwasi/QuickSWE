# Feature Request: Implement CUDA Parallel Reduction

## Summary

The `reduce.cu` file currently contains a working **CPU** `cpu_reduce_sum()`
function that serially sums a float array. A GPU function `gpu_reduce_sum()` is
stubbed out but not implemented — it simply returns `0.0f`.

Implement a proper **CUDA parallel reduction** that:

1. Uses shared memory for intra-block tree-based reduction.
2. Handles **arbitrary array sizes** — not just powers of 2.
3. Sums partial block results (either via a second kernel launch, a loop on the
   host, or recursive reduction).
4. Returns the correct total sum from `gpu_reduce_sum()`.

## Acceptance Criteria

- `gpu_reduce_sum(data, N)` returns the correct sum for:
  - N = 1000
  - N = 1023  (not a power of 2, one less than 1024)
  - N = 1024  (exact power of 2)
  - N = 100000 (large array)
- The GPU result must match the CPU result within a reasonable floating-point
  tolerance (relative error < 1e-4 for large arrays).
- For large arrays (N >= 100000), the GPU path should be **faster** than the
  CPU path when including only kernel execution time (not memory transfers).
  The test will time both and assert `gpu_time < cpu_time`.
- The existing `cpu_reduce_sum()` function must remain unchanged and continue
  to produce correct results.

## Current State

```c
float gpu_reduce_sum(const float *h_data, int N) {
    // TODO: implement parallel reduction
    return 0.0f;
}
```

## Design Hints

A typical approach:

1. **Kernel**: each block loads a tile into shared memory, then performs
   pairwise reduction (stride halving).
2. **Partial sums**: each block writes its partial sum to a device array.
3. **Final reduction**: either launch a second kernel on the partial sums, or
   copy them back to the host and sum there (the latter is simpler and fine
   for moderate grid sizes).

## Environment

- CUDA Toolkit 12.x
- Windows 11 / Linux
- Any NVIDIA GPU with compute capability >= 3.5
