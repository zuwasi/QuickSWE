# Task 030: B-Tree Node Split Bug

## Problem

A B-tree implementation has a bug in its node split operation. During a split,
the median key is correctly promoted to the parent, but it is also left in the
right child node, creating a duplicate. This corrupts the tree structure and
causes search to return incorrect results or fail to find existing keys.

## Expected Behavior

When splitting a full node, the median key should be moved to the parent and
the right child should only contain the keys after the median. No duplicate
keys should exist in the tree.

## Files

- `src/btree.py` — B-tree with insert, search, and in-order traversal
