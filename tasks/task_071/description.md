# B-Tree – Lazy Deletion with Incorrect Merge Rebalancing

## Problem

A B-tree (order 3) uses lazy deletion: removed keys are marked as deleted but
not immediately removed. A `compact()` operation triggers actual removal and
rebalancing. The merge logic during compaction has bugs.

Users report:

1. After marking several keys as deleted and calling `compact()`, some
   non-deleted keys disappear.
2. The merge operation during rebalancing incorrectly drops the separator key
   from the parent, losing a key.
3. After compact, `inorder()` traversal shows keys out of order.

## Files

- `src/btree_lazy.hpp` — B-tree with lazy deletion
- `src/main.cpp` — test driver
