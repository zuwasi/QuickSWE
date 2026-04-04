# Feature Request: Implement Spatial Hash Grid for Collision Detection

## Summary

The `particle_collision.cu` file contains:

- A working **CPU reference** brute-force collision detection (`cpu_find_collisions`)
  that checks all O(N²) pairs and returns pairs within a collision radius.
- A **particle system** with positions and velocities.
- A **stubbed** `gpu_spatial_hash_collisions()` function that currently returns
  zero collisions.

Implement a CUDA spatial hash grid for efficient collision detection:

1. **Hash particles into grid cells** based on position. Cell size should equal
   the collision radius so only neighboring cells need checking.
2. **Build a cell list**: for each cell, store indices of particles in that cell.
   Use atomic counters per cell.
3. **Detect collisions**: each thread handles one particle, checks its own cell
   plus all 26 neighboring cells (3D), computes distance to particles in those
   cells, and reports pairs within the collision radius.
4. **Handle cell overflow**: if a cell has more particles than the maximum per
   cell, don't crash — just skip the extras (and report overflow count).
5. **Handle boundary wrapping**: the domain wraps around (periodic boundary
   conditions), so particles at the edge should check cells on the opposite side.

## Acceptance Criteria

- All collision pairs found by CPU brute-force must also be found by GPU
  (no false negatives).
- No duplicate pairs (each pair reported once, with i < j).
- Handles cell overflow gracefully (no crash, reports overflow count).
- Particles at domain boundaries correctly check wrapped neighbor cells.
- Works for N=100, 500, 1000, 2000 particles.

## Current State

```c
int gpu_spatial_hash_collisions(const float *positions, int N,
                                 float radius, float domain_size,
                                 int *pairs, int max_pairs) {
    // TODO: implement spatial hash grid collision detection
    return 0;  // returns 0 collisions
}
```

## Environment

- CUDA Toolkit 12.x, any NVIDIA GPU with compute capability >= 3.5
