# Bug Report: Vector Addition Produces Wrong Results for Non-Multiple-of-BlockSize Arrays

## Summary

Our CUDA vector addition kernel produces correct results only when the
array size is an exact multiple of the block size. For any other size,
the last few elements are wrong (contain zeros or garbage).

## Symptoms

- Arrays of size 1024, 2048, etc. work fine.
- Array of size 1000 produces wrong results starting around element 960.
- Array of size 1025 has element 1024 as zero instead of the expected sum.
- The number of wrong elements seems related to `N % BLOCK_SIZE`.

## Expected Behavior

- Vector addition `C[i] = A[i] + B[i]` should work for any array size.
- All N elements should be correctly computed.
- No out-of-bounds memory accesses.

## Build Notes

Compile with: `nvcc -rdc=true -lcudadevrt -lm`
