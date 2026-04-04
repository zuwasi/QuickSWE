# Bug Report: BFS produces wrong distances and gets progressively slower

## Problem

The CUDA BFS implementation gives wrong distance values for some nodes in
the graph. It also gets progressively slower on larger graphs — a graph
with 5000 nodes takes far longer than expected, and 10000 nodes is
essentially stuck.

## How to Reproduce

```
./graph_bfs --nodes 100  --edges 500  --seed 42   # some distances wrong
./graph_bfs --nodes 1000 --edges 5000 --seed 42   # slow + wrong
./graph_bfs --nodes 5000 --edges 20000 --seed 42  # very slow
```

## Expected Behaviour

GPU BFS distances should match CPU BFS distances for all reachable nodes.
Performance should scale roughly linearly with graph size.

## Environment

- CUDA Toolkit 12.x, any GPU with compute capability >= 3.5
