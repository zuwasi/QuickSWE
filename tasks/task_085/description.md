# Bug Report: Quadtree Processing Hangs or Produces Wrong Results

## Summary

Our CUDA dynamic parallelism-based quadtree processor hangs or produces
wrong results depending on the tree configuration. It uses parent kernels
that launch child kernels to recursively process quadtree nodes.

## Symptoms

- Small trees (depth 1-2, 4-16 nodes) sometimes work correctly.
- Deeper trees (depth 3+, 64+ nodes) either:
  - Hang indefinitely (appears to deadlock)
  - Produce wrong accumulated values in the output buffer
- The wrong values look like partial results — some child contributions
  are missing while others appear duplicated.
- Reducing the number of parent threads sometimes makes it work, but
  using 1 thread defeats the purpose of parallelism.
- The hang seems to correlate with having many parent threads active
  simultaneously.

## What We've Tried

- Verified the CPU recursive reference produces correct results.
- Added `cudaDeviceSynchronize()` after child launches — makes the hang
  WORSE (almost always deadlocks now).
- Tried using separate streams for child kernels — didn't help.
- Reduced max recursion depth — still hangs at depth 3.

## Expected Behavior

- Quadtree nodes should be processed correctly at any depth up to 5.
- Each leaf node contributes its value to the output buffer.
- Internal nodes correctly aggregate child results.
- No deadlocks regardless of tree configuration.

## Build Notes

Must compile with: `nvcc -rdc=true -lcudadevrt`

## Environment

- CUDA Toolkit 12.x, any NVIDIA GPU with compute capability >= 3.5
  (dynamic parallelism requires >= 3.5)
