# HAMTrie – Incorrect Structural Sharing

## Problem

A Hash Array Mapped Trie (HAMT) implements a persistent (immutable) map.
`insert` and `remove` return new tries sharing structure with the original.

Users report:

1. After inserting into a new version, the original version is also modified —
   structural sharing copies the pointer but not the node, violating persistence.
2. The bitmap population count (`popcount`) used to index into the compressed
   child array is computed incorrectly, causing writes to wrong positions.
3. After removing a key from a derived version, the key also disappears from
   the original.

## Files

- `src/hamtrie.hpp` — HAMT persistent map
- `src/main.cpp` — test driver
