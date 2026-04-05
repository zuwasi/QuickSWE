# Bug Report: Custom GPU Memory Pool Allocator Corrupts Data

## Summary

Our custom GPU memory pool allocator implements a simple free-list
allocator on device memory. After several allocate/free cycles,
allocated blocks contain data from previously freed blocks, indicating
the free-block coalescing logic is merging blocks incorrectly.

## Symptoms

- First few allocations work fine.
- After freeing and re-allocating, new blocks overlap with existing ones.
- The coalescing of adjacent free blocks miscalculates the merged block
  size — it adds the headers' sizes but doesn't account for the header
  of the absorbed block, so the merged block is too small.
- The next-pointer update after coalescing points to the wrong location,
  skipping valid free blocks or creating cycles in the free list.

## Expected Behavior

- Allocations should never overlap.
- After coalescing, merged blocks should have correct size.
- All allocated data should be preserved through alloc/free cycles.

## Build Notes

Compile with: `nvcc -rdc=true -lcudadevrt -lm`
