# Patricia Trie – Incorrect Split Logic

## Problem

A Patricia (radix) trie stores strings with compressed edges. When inserting
a key that partially matches an existing edge, the edge must be split.

Users report:

1. Inserting "test" then "testing" works, but inserting "testing" then "test"
   fails to split the edge — "test" is not found after insertion.
2. Inserting "abc" and "abd" should split at "ab" but the prefix length
   calculation is wrong, causing one key to overwrite the other.
3. The `starts_with` prefix search returns false positives.

## Files

- `src/patricia_trie.hpp` — Patricia trie
- `src/main.cpp` — test driver
