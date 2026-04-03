# Feature Request: CUDA Tiled 1D Convolution with Halo Cells

## Summary

The `convolution.cu` file contains:

- A **CPU reference** 1D convolution function (`cpu_convolve`).
- A **naive CUDA kernel** (`naive_convolve_kernel`) that works but makes
  uncoalesced global memory accesses for every filter tap.
- A **stubbed tiled kernel** (`tiled_convolve_kernel`) that should use shared
  memory with proper halo (ghost) cell handling but currently does nothing.

Implement the tiled convolution kernel so that:

1. Each block loads a tile of input data plus halo cells (filter radius on
   each side) into shared memory.
2. Threads that fall in the halo region load boundary elements; out-of-bounds
   positions are zero-padded.
3. The convolution is computed from shared memory.
4. The GPU wrapper function `gpu_tiled_convolve()` calls the tiled kernel.

## Acceptance Criteria

- `gpu_tiled_convolve()` returns the correct result for:
  - Filter size 3 (radius 1)
  - Filter size 5 (radius 2)
  - Filter size 7 (radius 3)
- Input sizes tested: 256, 1000, 10000.
- The tiled GPU result must match the CPU reference within relative error
  < 1e-5.
- The naive kernel and CPU function must remain unchanged.

## Current State

```c
__global__ void tiled_convolve_kernel(const float *in, float *out,
                                       const float *filter, int N,
                                       int filter_size) {
    // TODO: implement tiled convolution with shared memory + halo cells
}

void gpu_tiled_convolve(const float *h_in, float *h_out,
                        const float *h_filter, int N, int filter_size) {
    // TODO: allocate, launch tiled_convolve_kernel, copy back
    // For now, just zero the output
    memset(h_out, 0, N * sizeof(float));
}
```

## Design Hints

1. Tile size = block size (e.g., 256).
2. Shared memory size = tile size + 2 × radius.
3. Left halo threads load `in[tile_start - radius + tid]` (clamped to 0 for
   out-of-bounds).
4. Right halo threads load the extra elements past the tile.
5. `__syncthreads()` before computing the convolution sum.

## Environment

- CUDA Toolkit 12.x
- Windows 11 / Linux
- Any NVIDIA GPU with compute capability >= 3.5
