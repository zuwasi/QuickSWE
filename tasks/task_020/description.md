# Task 020 – Topological Sort Fails to Detect Cycles

## Problem
The `topological_sort()` function performs a DFS-based topological sort.
It does not track temporary marks (in-progress state) during recursion,
so it cannot distinguish a back-edge (cycle) from a cross-edge. Cyclic
graphs silently produce an invalid ordering instead of raising an error.

## Expected Behaviour
- Cycles (including self-loops) are detected and raise `CyclicGraphError`.
- Valid DAGs continue to produce a correct topological ordering.

## Files
- `src/topo_sort.py` – the buggy sort
- `tests/test_topo_sort.py` – test suite
