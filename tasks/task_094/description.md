# Bug Report: Dynamic Parallelism Recursive Merge Sort Deadlocks

## Summary

Our CUDA dynamic parallelism merge sort launches child kernels to sort
sub-arrays recursively. It deadlocks for arrays larger than a few
hundred elements, and produces wrong results for smaller arrays.

## Symptoms

- Arrays under 64 elements sometimes sort correctly (single recursion level).
- Larger arrays hang indefinitely or produce partially sorted output.
- Child kernels are launched on the default (NULL) stream, which is shared
  across all threads in the parent. When multiple parent threads each
  launch children on stream 0 and then call `cudaDeviceSynchronize()`,
  deadlock occurs because each parent waits for ALL children, including
  other parents' children.
- The merge step reads from the source array before child sorts complete
  because `cudaDeviceSynchronize()` can deadlock, so the code falls through.
- The base case threshold is set to 1, meaning every single element gets
  its own kernel launch (extreme overhead and resource exhaustion).

## Expected Behavior

- Array should be sorted in ascending order matching `qsort` reference.
- Must work for arrays up to at least 4096 elements.
- No deadlocks.

## Build Notes

Compile with: `nvcc -rdc=true -lcudadevrt -lm`
