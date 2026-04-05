# Task 047: Deadlock Detector False Positive on Self-Loops

## Description

A deadlock detector uses a wait-for graph where edges represent "thread A waits
for thread B." It detects deadlocks by finding cycles in this graph. However, it
incorrectly treats self-loops (a thread listed as waiting on itself, e.g., due to
re-entrant lock bookkeeping) as deadlock cycles.

## Bug

The cycle detection algorithm marks a node as visited and then checks if any
successor is already visited — but it doesn't distinguish between visiting a
node that is on the current DFS path vs. one that was visited in a previous
traversal. More specifically, a self-edge (node → node) is immediately flagged
as a cycle.

## Expected Behavior

Self-loops should be ignored in deadlock detection. A true deadlock requires a
cycle of length ≥ 2 (involving at least two distinct threads).
