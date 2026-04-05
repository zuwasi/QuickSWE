# Bug Report: Persistent Kernel Misses Work Items

## Summary

Our persistent kernel processes a work queue using a grid-stride loop
pattern. Some work items are processed twice while others are skipped.

## Symptoms

- With fewer blocks than work items, some items show double processing.
- The grid-stride loop increment uses `blockDim.x` instead of
  `blockDim.x * gridDim.x`, so threads from the same block all
  advance together but different blocks process overlapping ranges.
- The atomic work counter that tracks completed items doesn't use
  the correct memory ordering, causing threads to read stale values
  and re-process items.
- Work items near the end of the queue are sometimes skipped because
  the termination check uses `>=` with the wrong count.

## Expected Behavior

- Every work item processed exactly once.
- Output should match CPU sequential processing.

## Build Notes

Compile with: `nvcc -rdc=true -lcudadevrt -lm`
