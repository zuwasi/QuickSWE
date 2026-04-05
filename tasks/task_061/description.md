# Red-Black Tree – Incorrect Uncle Color Check During Insertion

## Problem

A red-black tree implementation supports `insert`, `search`, `inorder`, and
validates its own invariants. The insertion fix-up procedure has bugs.

Users report:

1. Inserting a sorted sequence (1..10) creates an unbalanced tree that violates
   the black-height property.
2. The `validate()` method returns false after certain insertion patterns.
3. In-order traversal after insertions produces correct elements but the tree
   structure degenerates, causing O(n) lookup instead of O(log n).

The fix-up checks the uncle node's color but has an error in which case it
selects — it confuses the uncle-is-red case with the uncle-is-black case,
applying recoloring when it should rotate and vice versa.

## Files

- `src/rbtree.hpp` — red-black tree implementation (~250 lines)
- `src/main.cpp` — test driver

## Expected Behaviour

- All five RB-tree invariants are maintained after every insertion.
- `validate()` returns true after any sequence of insertions.
- The tree height is O(log n).
