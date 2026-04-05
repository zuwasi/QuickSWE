# Bug Report: Tiled GEMM With Double Buffering Gives Wrong Results

## Summary

Our optimized GEMM kernel uses shared memory tiling with double buffering
to overlap global memory loads with computation. Results don't match the
CPU reference for any non-trivial matrix size.

## Symptoms

- The first tile's computation is correct, but subsequent tiles are wrong.
- The double buffering swap uses the wrong buffer index — the write
  buffer and compute buffer are the same, causing data to be overwritten
  before it's consumed.
- The tile loading uses `K` as the leading dimension for matrix A instead
  of the actual leading dimension (which is K for row-major A).
- When loading the next tile, the `__syncthreads()` is placed after
  starting computation instead of after the load, so threads may read
  the buffer while it's still being filled.
- The tile index for matrix B uses `blockIdx.x` instead of `blockIdx.y`
  for the column offset.

## Expected Behavior

- C[M x N] = A[M x K] * B[K x N] should match CPU naive GEMM.
- Should work for any M, N, K that are multiples of tile size.

## Build Notes

Compile with: `nvcc -rdc=true -lcudadevrt -lm`
