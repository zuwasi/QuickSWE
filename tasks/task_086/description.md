# Bug Report: Multi-GPU Processing Produces Partial Results

## Summary

Our multi-GPU vector processing splits work across available GPUs (or
simulates multi-GPU with streams on one device), but the results are
partially wrong. The overlap regions where data is exchanged between
partitions contain stale values.

## Symptoms

- Single-GPU mode works correctly.
- Multi-partition mode produces wrong values at partition boundaries.
- The halo exchange between partitions doesn't wait for the compute
  kernel to finish before copying boundary data.
- Stream synchronization uses the wrong stream — copies are issued on
  the default stream instead of the compute stream, so they can
  execute before the kernel writes the boundary values.
- The final gather doesn't synchronize all streams before reading
  results.

## Expected Behavior

- All elements should match CPU reference regardless of partition count.
- Halo exchange should properly synchronize compute and copy operations.

## Build Notes

Compile with: `nvcc -rdc=true -lcudadevrt -lm`
