# Constexpr Ray Tracer – Incorrect Reflection Vector

## Problem

A constexpr ray tracer computes ray-sphere intersections and reflections at
compile time. The reflection and intersection computations have bugs.

Users report:

1. The reflection formula is wrong: `reflect(d, n)` should give `d - 2*(d·n)*n`
   but the implementation uses `d + 2*(d·n)*n`, producing vectors pointing in
   the wrong direction.
2. The sphere intersection test uses the wrong discriminant formula, rejecting
   valid intersections.
3. The ray-sphere intersection returns the farther hit point instead of the
   nearest, causing incorrect rendering.

## Files

- `src/raytracer.hpp` — constexpr vector math and ray tracer
- `src/main.cpp` — test driver (runtime verification of constexpr results)
