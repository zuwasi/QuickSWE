# Pool Allocator – Incorrect Free-List Coalescing

## Problem

A pool allocator manages a fixed-size memory pool. It supports `allocate(size)`,
`deallocate(ptr)`, and coalesces adjacent free blocks. The coalescing logic has bugs.

Users report:

1. After allocate-deallocate cycles, the allocator reports fragmentation even
   though all memory has been freed — adjacent free blocks are not merged.
2. Allocating after several deallocations fails with "out of memory" even though
   enough total free space exists (but is fragmented because coalescing failed).
3. The `available()` method undercounts free space after coalescing attempts.

## Files

- `src/pool_allocator.hpp` — pool allocator
- `src/main.cpp` — test driver
