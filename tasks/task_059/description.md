# Bug: Incorrect Hash Table with Chaining

## Description

A hash table implementation using linked-list chaining has two bugs:

1. **Negative index from hash function**: The hash function computes `key % capacity` but doesn't handle negative keys. In C, the `%` operator can return negative values for negative operands, leading to negative array indices and undefined behavior (crashes or corrupted data).

2. **Resize doesn't rehash**: When the table grows (load factor > 0.75), it allocates a larger bucket array but simply copies the old bucket pointers without rehashing entries. Since entries' bucket assignment depends on the capacity, items end up in wrong buckets after resize, making them unfindable by `ht_get`.

## Expected Behavior

- `ht_insert(table, -5, 100)` followed by `ht_get(table, -5)` returns 100.
- After inserting enough items to trigger a resize, all previously inserted items remain findable.

## Actual Behavior

- Inserting a negative key causes a crash or silent corruption.
- After resize, some or all entries become unreachable because they sit in buckets that no longer correspond to their hash.

## Files

- `src/hashtable.h` — struct definitions
- `src/hashtable.c` — hash table implementation with bugs
- `src/main.c` — test driver that prints results
