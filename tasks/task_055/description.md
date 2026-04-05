# Hash Map – Incorrect Linear Probing Collision Resolution

## Problem

A simple open-addressing hash map uses linear probing for collision resolution.
It supports `insert`, `get`, `remove`, `contains`, and `size`.

Users report:

1. After inserting keys that hash to the same bucket, `get()` fails to find some
   keys even though they were successfully inserted.
2. After removing a key, looking up a different key that was placed after the
   removed key (due to collision) returns "not found" — the probe sequence stops
   at the deleted slot instead of continuing.
3. Reinsertion after deletion sometimes creates duplicates.

## Files

- `src/hashmap.hpp` — HashMap implementation
- `src/main.cpp` — test driver

## Expected Behaviour

- Linear probing must skip over tombstone (deleted) entries during lookup.
- Insert must reuse tombstone slots but still check for existing keys further
  along the probe chain to prevent duplicates.
- The map must handle wrap-around at table boundaries correctly.
