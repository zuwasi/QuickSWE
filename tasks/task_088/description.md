# Bug Report: Unified Memory Iterative Solver Produces Wrong Results

## Summary

Our iterative Jacobi solver uses CUDA unified memory with prefetch hints
to overlap data movement and computation. The solver converges to wrong
values or doesn't converge at all.

## Symptoms

- The Jacobi iteration produces wrong residuals after the first iteration.
- The prefetch hints prefetch the output buffer to the GPU *before*
  the CPU has finished reading the previous iteration's results.
- The ping-pong buffer swap is done incorrectly — after prefetching
  buffer A to GPU for writing, the code reads from buffer A on GPU
  instead of buffer B, so it reads the data being overwritten.
- The residual computation on CPU accesses GPU-resident pages without
  prefetching back, causing implicit page faults and stale data.

## Expected Behavior

- Jacobi iteration should converge to the correct solution.
- Residual should decrease monotonically.
- Prefetch hints should not cause data races between read and write buffers.

## Build Notes

Compile with: `nvcc -rdc=true -lcudadevrt -lm`
