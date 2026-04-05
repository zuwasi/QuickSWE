# Task 031: Consistent Hash Ring Lookup Bug

## Problem

A consistent hash ring implementation for distributed hash tables has a bug in
its node lookup. After using `bisect` to find the insertion point for a key's
hash, the ring wraps around incorrectly — when the key's hash is beyond the
last node on the ring, it should wrap to the first node (index 0), but instead
it wraps to the wrong position, causing keys to be assigned to the wrong node.

## Expected Behavior

When a key is hashed and looked up on the ring, the `bisect_right` result
should be used with modular arithmetic to find the next node clockwise on the
ring. If the index equals the length of the ring, it should wrap to index 0.

## Files

- `src/consistent_hash.py` — Consistent hashing ring with virtual nodes
