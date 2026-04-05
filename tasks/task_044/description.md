# Task 044: Reactive Dataflow Engine Diamond Dependency Glitch

## Description

A reactive computation graph with Signal and Computed nodes has a "glitch" problem
with diamond dependencies. When A feeds into both B and C, and both feed into D,
updating A causes D to recompute twice: once when B updates (with stale C) and
once when C updates. This produces an intermediate inconsistent state.

## Bug

The propagation algorithm eagerly recomputes dependents without topological ordering.
When a signal changes, it immediately notifies all dependents depth-first, causing
downstream nodes with multiple changed parents to see inconsistent intermediate states.

## Expected Behavior

The engine should use topological ordering (or a batching/scheduling mechanism) to
ensure that a node is only recomputed after ALL its dependencies have been updated.
This prevents glitches where stale values are observed.
