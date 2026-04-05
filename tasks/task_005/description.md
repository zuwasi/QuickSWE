# Task 005: Trie Autocomplete Ordering

## Problem

The `Trie` class supports `insert`, `search`, and `autocomplete` operations. The `autocomplete(prefix)` method should return all words with the given prefix in **alphabetical order**, but the current implementation uses DFS without sorting children, resulting in arbitrary/insertion-dependent ordering.

## Expected Behavior

- `autocomplete("app")` on a trie containing ["apple", "application", "apply"] should return `["apple", "application", "apply"]` (alphabetical)
- The ordering should be consistent regardless of insertion order
- `search()` and `starts_with()` should continue to work correctly

## Files

- `src/trie.py` — Trie implementation with insert, search, autocomplete
- `tests/test_trie.py` — Test suite
