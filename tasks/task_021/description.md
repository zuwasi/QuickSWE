# Task 021: Red-Black Tree Deletion Bug

## Problem

A red-black tree implementation loses nodes after deletion when the uncle node is black
and a double rotation is required. The `_delete_fixup` method incorrectly handles the
case where the sibling's children are both black — it fails to properly recolor the
parent and sibling, which leaves the tree in an invalid state and causes nodes to become
unreachable during subsequent operations.

## Expected Behavior

After deleting any node, the red-black tree properties must be maintained:
1. Every node is either red or black
2. The root is black
3. Every path from root to leaf has the same number of black nodes
4. No two consecutive red nodes exist

All remaining nodes must be reachable via in-order traversal.

## Files

- `src/rbtree.py` — Red-black tree with insert and delete operations
