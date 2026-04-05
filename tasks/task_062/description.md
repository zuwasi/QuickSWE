# B+ Tree – Incorrect Key Redistribution During Underflow

## Problem

A B+ tree (order 4) supports `insert`, `search`, `range_query`, and `remove`.
Deletion triggers redistribution or merging when a node underflows.

Users report:

1. Removing keys causes the tree to lose elements — `search()` returns false
   for keys that were never removed.
2. After removing enough keys to trigger an underflow, the parent separator
   key is not updated correctly during redistribution from a sibling.
3. Range queries after deletions return incomplete results.

## Files

- `src/bplus_tree.hpp` — B+ tree implementation
- `src/main.cpp` — test driver

## Expected Behaviour

- After redistribution, the parent separator key must equal the first key of
  the right child.
- All non-deleted keys must remain findable.
- Range queries must return all keys in the given range.
