# Feature Request: Implement High-Performance Tiled Matrix Multiply

## Summary

The `tiled_gemm.cu` file contains:

- A working **CPU reference** GEMM (`cpu_gemm`).
- A working but **naive GPU kernel** (`naive_gemm_kernel`) that does one
  multiply-add per thread with no tiling.
- A **stubbed function** `tiled_gemm()` that currently falls back to
  the naive kernel.

Implement a fully tiled GEMM using shared memory tiles AND register-level
blocking where each thread computes a 4×4 sub-tile of the output matrix.

## Acceptance Criteria

- `tiled_gemm()` must produce results matching `cpu_gemm()` within
  floating-point tolerance (max element-wise error < 1e-2) for:
  - 64×64  × 64×64
  - 100×100 × 100×100  (non-tile-aligned)
  - 256×128 × 128×256
  - 500×300 × 300×400  (non-aligned, rectangular)
- The existing `cpu_gemm()` and `naive_gemm_kernel()` must remain unchanged.
- Must handle arbitrary M, N, K (not just multiples of the tile size).

## Current State

```c
void tiled_gemm(const float *A, const float *B, float *C,
                int M, int N, int K) {
    // TODO: implement tiled GEMM with register blocking
    // Falls back to naive kernel for now
    ...
}
```

## Design Hints

1. Choose a tile size (e.g., TILE=32).  Each thread-block loads a
   TILE×TILE sub-matrix of A and B into shared memory.
2. Each thread computes a THREAD_TILE×THREAD_TILE (4×4) sub-tile of C,
   accumulating into registers across K-dimension tiles.
3. Guard shared memory loads and stores for boundary tiles where
   M, N, or K is not a multiple of TILE.

## Environment

- CUDA Toolkit 12.x
- Windows 11 / Linux
- Any NVIDIA GPU with compute capability >= 3.5
