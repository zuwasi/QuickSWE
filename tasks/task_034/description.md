# Task 034: Mergeable Heap Bug

## Problem

A heap-based priority queue has a bug in its `merge()` operation. After
concatenating two heaps' internal arrays, it runs `_heapify()` starting from
the wrong index — it starts from index 0 (the root) and sifts down, but the
standard heapify algorithm requires starting from the last non-leaf node
(index `n//2 - 1`) and working backwards to index 0. Starting from the wrong
position fails to establish the heap property.

## Expected Behavior

After merging two heaps, `extract_min()` should always return elements in
non-decreasing order, and the heap property should be maintained.

## Files

- `src/merge_heap.py` — Mergeable min-heap implementation
