# Bug Report: Parallel Reduction With Warp Shuffle Gives Wrong Sum

## Summary

Our CUDA parallel reduction kernel uses warp-level shuffle intrinsics
for the final warp reduction but produces incorrect sums. The shared
memory portion seems fine, but the warp shuffle phase loses values.

## Symptoms

- Results are consistently lower than the CPU reference sum.
- The error is not random — it appears that some lanes' values are
  not included in the final reduction.
- The warp shuffle mask parameter appears incorrect, causing some
  threads to not participate in the shuffle operations.
- The reduction works correctly for arrays smaller than one warp (32)
  but fails for larger arrays.

## Expected Behavior

- `sum(array[0..N-1])` should match the CPU reference within
  floating-point tolerance.
- All elements should contribute to the final sum.

## Build Notes

Compile with: `nvcc -rdc=true -lcudadevrt -lm`
