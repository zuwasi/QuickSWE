# Bug Report: Shortest Path Returns Incorrect Distances

## Summary

Our shortest path implementation (Dijkstra's algorithm) returns incorrect distances for certain graph configurations. Simple graphs with obvious shortest paths work correctly, but more complex graphs with multiple possible paths produce wrong results.

## Steps to Reproduce

1. Create a weighted graph with a "diamond" pattern — multiple paths between two nodes with different weights
2. Run the shortest path algorithm
3. The returned distance is sometimes higher than the actual shortest path

## Expected Behavior

The algorithm should return the shortest distance between two nodes, considering all possible paths.

## Actual Behavior

For certain graphs, the returned distance is suboptimal. The path found is valid but not the shortest one.

## Additional Notes

- Simple graphs (linear chains, trees) work perfectly
- The issue seems related to graphs with many interconnected nodes and varying edge weights
- We have a custom MinHeap priority queue — could that be the issue?
- The ASCII graph visualizer module was recently added and is quite complex, but visualization output looks correct
- We've verified that edges are being added correctly to the graph
- Sometimes we get errors when nodes have equal-weight edges — might be a comparison issue?

## Example

Graph where bug manifests:
```
A --1--> B --1--> D
A --3--> C --1--> D (total: 4)
B --1--> C (shortcut)
```
Expected shortest A->D: 2 (A->B->D)
Got: sometimes returns a longer path
