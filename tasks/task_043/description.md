# Task 043: CRDT G-Counter Merge Bug

## Description

A Conflict-free Replicated Data Type (CRDT) implementation provides G-Counter
(grow-only counter) and PN-Counter (positive-negative counter). The G-Counter
merge function should take the maximum of each replica's count, but incorrectly
takes the minimum, causing counts to be lost after merge.

## Bug

In `GCounter.merge()`, the per-replica counts are combined using `min()` instead
of `max()`. The correct semantics for G-Counter merge is to take the maximum
count for each replica, since counts only grow.

## Expected Behavior

After merging two G-Counter states, each replica's count should be the maximum
of the two values seen for that replica.
