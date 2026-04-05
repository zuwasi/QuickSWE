# Task 015 – Dijkstra Returns Wrong Path for Zero-Weight Edges

## Problem
The `dijkstra()` function computes shortest paths in a weighted graph.
When the graph contains edges with weight zero, the algorithm may
re-process already-visited nodes and produce incorrect shortest paths
or wrong total distances.

## Expected Behaviour
- Zero-weight edges are valid and must be handled correctly.
- A visited node must never be re-processed.
- The returned path must truly be the shortest.

## Files
- `src/dijkstra.py` – the buggy algorithm
- `tests/test_dijkstra.py` – test suite
