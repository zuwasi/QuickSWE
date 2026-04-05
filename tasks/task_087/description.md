# Bug Report: Cooperative Groups Reduction Wrong for Non-Warp-Multiple Block Sizes

## Summary

Our cooperative groups based reduction kernel uses `tiled_partition` to
create sub-warp tiles for efficient reduction. It works for block sizes
that are exact multiples of the tile size but fails for other
configurations.

## Symptoms

- Block size 256 with tile size 32 works correctly.
- Block size 256 with tile size 16 produces wrong results.
- The tile partition size is hardcoded to 32 but the inter-tile
  reduction assumes a different tile size, causing misaligned reads
  in the shared memory aggregation step.
- The lane index within the tile is computed using `threadIdx.x % 32`
  instead of using the cooperative group's `thread_rank()`, so when
  the tile size is not 32, the wrong lane is selected for broadcast.

## Expected Behavior

- Reduction should produce correct sum for any valid tile size
  (1, 2, 4, 8, 16, 32).
- The tile-level reduction should use the tile's own API for
  thread rank and shuffle operations.

## Build Notes

Compile with: `nvcc -rdc=true -lcudadevrt -lm`
