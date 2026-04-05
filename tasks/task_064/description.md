# Skip List – Incorrect Level Probability Distribution

## Problem

A skip list implements an ordered set with probabilistic balancing. Each node
gets a random level, with level `k+1` chosen with probability `p=0.5` given
level `k`.

Users report:

1. The random level generator always returns the same level (or never exceeds
   level 1), making the skip list degenerate to a linked list.
2. Search sometimes misses existing keys because the forward pointer update
   during insert does not cover all levels correctly.
3. The `remove` function does not update the list's max level when the highest-
   level node is removed, causing null pointer dereferences on subsequent operations.

## Files

- `src/skiplist.hpp` — skip list implementation
- `src/main.cpp` — test driver (uses a fixed seed for deterministic tests)
