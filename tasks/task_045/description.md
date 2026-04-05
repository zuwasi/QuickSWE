# Task 045: LSM-Tree Tombstone Handling During Compaction

## Description

An LSM-tree (Log-Structured Merge-Tree) implementation uses multiple sorted levels.
Writes go to an in-memory memtable, which is flushed to Level 0 when full. Compaction
merges Level N into Level N+1. Deletes are represented as tombstone markers.

## Bug

During compaction, tombstone markers are discarded instead of being propagated to
lower levels. This means if a key exists in a lower level that wasn't part of the
compaction, the tombstone is lost and the deleted key "resurrects" — it becomes
visible again on subsequent reads.

## Expected Behavior

Tombstones must be propagated during compaction to all levels. A tombstone can only
be safely discarded during compaction of the lowest level (where no older version
can exist below).
