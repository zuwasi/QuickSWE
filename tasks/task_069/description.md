# Bug Fix: CUDA Matrix Transpose — Shared Memory Bank Conflicts & Wrong Indexing

## Summary

The `transpose.cu` file implements a tiled matrix transpose using CUDA shared
memory. There are two bugs:

1. **Shared memory bank conflicts**: The shared memory tile is declared as
   `__shared__ float tile[TILE_SIZE][TILE_SIZE]`. Because TILE_SIZE (32)
   matches the number of memory banks, every warp accessing a column hits the
   same bank, serialising the accesses. The fix is to add +1 padding:
   `__shared__ float tile[TILE_SIZE][TILE_SIZE + 1]`.

2. **Thread index swap on write-back**: When writing the transposed tile back
   to global memory, the x and y thread indices are swapped, placing data in
   the wrong output location. This produces an incorrect result for
   **non-square** matrices (for square matrices the symmetric bug may
   accidentally give a plausible-looking result in certain cases, but the
   transposition is still wrong).

## Acceptance Criteria

- The transpose must produce the correct result for **non-square** matrices,
  verified against a CPU reference transpose.
- Supported test sizes: 64×128, 128×64, 100×200, 256×256, 1×1024.
- The GPU result must match the CPU result **exactly** (element-wise, float
  equality — no tolerance needed because we only copy/reorder, no arithmetic).
- The kernel must still compile and run without errors after the fix.

## Current Bugs (in `transpose_kernel`)

```c
// BUG 1: bank conflicts — no padding
__shared__ float tile[TILE_SIZE][TILE_SIZE];

// BUG 2: write-back indices swapped
int out_x = blockIdx.y * TILE_SIZE + threadIdx.y;  // should be threadIdx.x
int out_y = blockIdx.x * TILE_SIZE + threadIdx.x;  // should be threadIdx.y
out[out_y * N + out_x] = tile[threadIdx.x][threadIdx.y];
```

## Environment

- CUDA Toolkit 12.x
- Windows 11 / Linux
- Any NVIDIA GPU with compute capability >= 3.5
