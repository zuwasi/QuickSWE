# Bug Report: Prefix Sum (Exclusive Scan) Off by One

## Summary

Our CUDA exclusive prefix sum kernel produces results that are shifted
by one position compared to the CPU reference. The last element is wrong
and all intermediate results are off.

## Symptoms

- The output appears to be an inclusive scan instead of exclusive scan.
- `output[0]` should be 0 for exclusive scan, but contains `input[0]`.
- Every subsequent element is the sum including the current element
  rather than excluding it.
- The up-sweep phase seems correct but the down-sweep has an
  incorrect offset when converting from inclusive to exclusive scan.
- The identity element (0) is not properly inserted at position 0.

## Expected Behavior

- Exclusive scan: `output[i] = sum(input[0..i-1])`, `output[0] = 0`.
- Should work for arrays up to block size (single-block implementation).

## Build Notes

Compile with: `nvcc -rdc=true -lcudadevrt -lm`
