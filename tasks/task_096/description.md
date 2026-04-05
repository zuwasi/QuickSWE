# Bug Report: GPU BFS Produces Wrong Distances for Some Vertices

## Summary

Our CUDA BFS traversal on a CSR graph uses a warp-centric approach where
each warp cooperatively processes one frontier vertex's neighbors. Some
vertices end up with wrong distances or are never visited.

## Symptoms

- Vertices close to the source have correct distances.
- Vertices 3+ hops away frequently have wrong (too large) distances.
- Some reachable vertices remain at distance -1 (unvisited).
- The frontier queue append uses a non-atomic increment, causing
  multiple warps to overwrite each other's frontier entries.
- The visited check uses a non-atomic read-modify-write, so two warps
  can both think a vertex is unvisited, causing duplicate processing
  and frontier overflow.
- The warp-level neighbor distribution uses `lane_id` offset but
  doesn't account for warps that started at different positions in
  the adjacency list.

## Expected Behavior

- BFS distances should match CPU BFS for all reachable vertices.
- Every reachable vertex should be visited exactly once.

## Build Notes

Compile with: `nvcc -rdc=true -lcudadevrt -lm`
