# Bug Report: N-Body GPU Simulation Diverges From Reference

## Summary

Our CUDA N-body simulation uses a direct all-pairs force calculation
but has bugs in the force accumulation and position integration that
cause the simulation to diverge from the CPU reference.

## Symptoms

- After even a single timestep, positions diverge significantly.
- The force calculation uses `r^2` in the denominator instead of `r^3`
  for the gravitational force magnitude (force should be `G*m1*m2/r^2`
  but the direction vector already has magnitude r, so we need to
  divide by `r^3` to get the force vector components).
- The softening factor is squared in the wrong place — added to `r`
  before squaring instead of added to `r^2`.
- The velocity update applies the force in the wrong direction (adds
  instead of subtracts for the j-to-i force direction).
- The position update uses the old velocity instead of the updated
  velocity (leapfrog integration requires half-step velocity).

## Expected Behavior

- After N timesteps, positions should match CPU reference within tolerance.
- Energy should be approximately conserved.

## Build Notes

Compile with: `nvcc -rdc=true -lcudadevrt -lm`
