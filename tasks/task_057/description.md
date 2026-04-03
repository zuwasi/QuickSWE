# Bug Report: Race Condition in CUDA Histogram with Shared Memory

## Summary

The `histogram` CUDA kernel computes a histogram of byte values (0–255) in an
input array. It uses shared memory for per-block partial histograms, then
merges them into the global histogram via `atomicAdd`. However, the shared
memory is **never initialized to zero**, and there is a **missing
`__syncthreads()`** barrier, producing incorrect and non-deterministic results.

## Steps to Reproduce

1. Compile `src/histogram.cu` with `nvcc`.
2. Run with `--size 10000 --seed 42` to generate a deterministic input.
3. Compare the GPU histogram output against a CPU reference histogram.

## Expected Behavior

The GPU histogram must exactly match the CPU reference histogram for every bin
(0–255).

## Actual Behavior

- Many bins have wildly wrong counts (too high or too low).
- Results are **non-deterministic** across runs because shared memory contains
  garbage values and threads race on un-initialized locations.

## Root Cause Analysis

There are **two bugs** in the histogram kernel:

1. **Shared memory not zeroed**: The kernel declares
   `__shared__ int s_hist[256];` but never sets all 256 entries to zero before
   accumulating. Shared memory is **not** auto-initialized in CUDA; its
   contents are undefined on entry. This means every block starts with garbage
   counts.

2. **Missing `__syncthreads()` after initialization**: Even after adding the
   zeroing loop, all threads in a block must synchronize before any thread
   begins incrementing bins. Without a `__syncthreads()` barrier, some threads
   may start accumulating into `s_hist` while other threads are still zeroing
   it, causing a data race.

   A second `__syncthreads()` is also needed **after** the accumulation loop
   and **before** the merge into global memory, so that all threads finish
   writing to shared memory before any thread copies the partial histogram out.

### Fix Outline

```c
// 1. Zero shared memory
for (int bin = threadIdx.x; bin < 256; bin += blockDim.x)
    s_hist[bin] = 0;

__syncthreads();  // <-- BUG 2: this barrier is missing

// 2. Accumulate
for (int idx = ...; idx < N; idx += ...)
    atomicAdd(&s_hist[data[idx]], 1);

__syncthreads();  // <-- also missing before merge

// 3. Merge to global
for (int bin = threadIdx.x; bin < 256; bin += blockDim.x)
    atomicAdd(&hist[bin], s_hist[bin]);
```

## Environment

- CUDA Toolkit 12.x
- Windows 11 / Linux
- Any NVIDIA GPU with compute capability >= 3.5
