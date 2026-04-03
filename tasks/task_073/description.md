# Feature Request: Implement CUDA Bitonic Sort for Arbitrary-Length Arrays

## Summary

The `bitonic_sort.cu` file contains:

- A working **CPU reference** sort (`cpu_sort` — just calls `qsort`).
- A **stubbed GPU function** `gpu_bitonic_sort()` that currently copies input
  to output unchanged.

Implement a full CUDA bitonic sort that:

1. Pads the input array to the next power of 2 with `FLT_MAX` sentinel values.
2. Runs the full bitonic sort network on the GPU (nested loops over stages
   and steps, each step is a kernel launch or a single kernel with
   synchronisation).
3. Copies back only the first N (valid) elements to the output.

## Acceptance Criteria

- `gpu_bitonic_sort()` must produce a correctly sorted (ascending) output for:
  - N = 100
  - N = 1000
  - N = 1023 (one less than a power of 2)
  - N = 1024 (exact power of 2)
  - N = 5000 (larger, non-power-of-2)
- The GPU result must match the CPU-sorted result exactly (element-wise).
- The existing `cpu_sort()` function must remain unchanged.

## Current State

```c
void gpu_bitonic_sort(const float *h_in, float *h_out, int N) {
    // TODO: implement bitonic sort
    memcpy(h_out, h_in, N * sizeof(float));
}
```

## Design Hints

1. Compute `padded_N = next_power_of_2(N)`.
2. Allocate device array of `padded_N` floats, fill first N from input, rest
   with `FLT_MAX`.
3. Bitonic sort network: for each stage `k` (1..log2(padded_N)), for each
   step `j` (k..0), launch a kernel that compares and swaps pairs at
   distance `1 << j`, alternating ascending/descending per sub-sequence of
   size `1 << (k+1)`.
4. Copy first N elements back.

## Environment

- CUDA Toolkit 12.x
- Windows 11 / Linux
- Any NVIDIA GPU with compute capability >= 3.5
