# Tarjan's SCC – Incorrect Lowlink Update

## Problem

An implementation of Tarjan's algorithm finds strongly connected components in a
directed graph. The lowlink update has bugs.

Users report:

1. Simple cycles are detected correctly, but complex graphs with multiple SCCs
   produce too many or too few components.
2. Cross edges (to already-finished nodes not on the stack) incorrectly update
   the lowlink, causing unrelated nodes to be grouped into the same SCC.
3. A DAG is incorrectly reported as having SCCs of size > 1.

## Files

- `src/tarjan.hpp` — Tarjan's SCC implementation
- `src/main.cpp` — test driver
