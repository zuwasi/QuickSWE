# Bug Report: Molecular Dynamics Neighbor List Produces Wrong Forces

## Summary

Our CUDA molecular dynamics simulation uses a Lennard-Jones potential
with a neighbor list for efficient force calculation. The forces are
wrong, causing atoms to fly apart or collapse.

## Symptoms

- Forces are much larger than expected, causing numerical instability.
- The distance calculation for the neighbor list cutoff uses `r`
  (distance) instead of `r^2` for comparison with `cutoff^2`,
  requiring an expensive sqrt that the code doesn't perform.
- The LJ force computation uses `sigma/r` raised to the wrong power
  — uses `pow(sigma_r, 6)` for the `r^12` term instead of
  `pow(sigma_r, 12)`.
- The force direction is not normalized — applies `F * dr` instead
  of `F * dr / r`, doubling the distance factor.
- The neighbor list includes self-interactions (i == j), adding a
  singularity to the force calculation.
- Newton's third law is not properly applied — the code adds force
  to particle i but doesn't subtract from particle j, or subtracts
  with wrong sign.

## Expected Behavior

- Total force on each particle should match CPU reference.
- Total momentum should be approximately conserved.
- No NaN or Inf values in forces.

## Build Notes

Compile with: `nvcc -rdc=true -lcudadevrt -lm`
