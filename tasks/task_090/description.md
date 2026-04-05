# Bug Report: Predicated Warp Computation Gives Wrong Results

## Summary

Our kernel uses warp-level voting and ballot to optimize a conditional
computation. Threads that satisfy a predicate compute one formula, others
compute a different one. The warp ballot mask is used to select which
threads participate in a shuffle-based reduction, but the mask is wrong.

## Symptoms

- The active mask from `__ballot_sync` uses `0x0000FFFF` instead of
  `0xFFFFFFFF`, so only the lower 16 lanes participate in voting.
- The predicated computation uses `__shfl_sync` with the wrong mask,
  causing inactive threads' values to be included in the reduction.
- When all threads in a warp take the same branch, results are correct.
- When threads diverge (mixed predicate), results are wrong.

## Expected Behavior

- Each element should be processed according to its predicate.
- The warp-level aggregation should only include active threads.

## Build Notes

Compile with: `nvcc -rdc=true -lcudadevrt -lm`
