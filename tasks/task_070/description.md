# Bug Fix: CUDA Prefix Sum (Scan) — Off-by-One & Missing Inter-Block Sync

## Summary

The `prefix_sum.cu` file implements a Blelloch-style exclusive parallel prefix
sum (scan) in CUDA. There are two bugs:

1. **Off-by-one in up-sweep stride**: The up-sweep loop's stride calculation
   uses `stride < blockDim.x` instead of `stride <= blockDim.x / 2` (or
   equivalently `stride < blockDim.x`  but starting from the wrong value),
   causing the last reduction step to be skipped. The root element of each
   block's tree is never fully reduced.

2. **Missing inter-block combination**: When the array spans multiple blocks,
   each block independently produces a local prefix sum but the block-level
   partial sums are never propagated. A correct implementation must:
   - Collect per-block totals.
   - Run a scan on those totals.
   - Add the scanned block offset to every element in subsequent blocks.

## Acceptance Criteria

- Exclusive prefix sum must be correct for:
  - N = 128 (fits in one block)
  - N = 1000 (multiple blocks, arbitrary size)
  - N = 10000 (many blocks)
- GPU result must match CPU reference (exact integer match — inputs are ints).
- The binary prints MATCH=1 when correct.

## Current Bugs

```c
// BUG 1 — up-sweep: stride starts at 1 but loop condition is wrong
for (int stride = 1; stride < blockDim.x; stride *= 2) {
    // should be: stride <= blockDim.x / 2
    // OR the indexing inside uses (2*stride - 1) which goes out of range
    ...
}

// BUG 2 — multi-block: block sums are stored but never scanned/added back
```

## Environment

- CUDA Toolkit 12.x
- Windows 11 / Linux
- Any NVIDIA GPU with compute capability >= 3.5
