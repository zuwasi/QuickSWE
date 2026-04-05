# Task 041: Buddy Allocator Incorrect Coalescing

## Description

A buddy memory allocator splits and merges power-of-two-sized blocks. On free, it
should coalesce a freed block with its buddy if the buddy is also free. The buddy
of a block at address `addr` with size `2^k` is at `addr XOR 2^k`.

## Bug

The buddy address calculation uses the wrong XOR mask. Instead of XOR-ing with
the block size (`2^k`), it XOR-s with `2^(k-1)`, which computes the wrong buddy
address. This causes non-buddy blocks to be merged, corrupting the free list
and potentially overlapping allocated blocks.

## Expected Behavior

The buddy of block at `addr` of order `k` should be at `addr XOR (1 << k)`.
When this buddy is free and of the same order, they should be merged into
a block of order `k+1`.
