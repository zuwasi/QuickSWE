# Bug Report: Ray-AABB Intersection Test Returns Wrong Hit Results

## Summary

Our CUDA ray tracer tests rays against axis-aligned bounding boxes (AABBs)
in a flat BVH structure. Many rays that should hit report misses, and
some rays report hits at wrong distances.

## Symptoms

- Rays along axis-aligned directions sometimes work, diagonal rays fail.
- The ray-AABB slab test has swapped min/max when the ray direction
  component is negative — doesn't handle the case where `invDir < 0`
  causes `tmin > tmax` for that slab.
- The BVH traversal stack push/pop is reversed — pushes with post-increment
  but pops with post-decrement, causing the stack pointer to go out
  of bounds or skip nodes.
- The closest hit distance is initialized to 0 instead of FLT_MAX,
  so no intersection can beat it.
- The leaf node check uses `>=` instead of `==` for the node index,
  skipping leaf nodes.

## Expected Behavior

- Every ray-AABB intersection that geometrically exists should be detected.
- Hit distances should match CPU reference implementation.

## Build Notes

Compile with: `nvcc -rdc=true -lcudadevrt -lm`
