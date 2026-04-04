# Bug Report: N-body Simulation Instability

## Summary

Our CUDA N-body gravitational simulation is producing completely wrong results.
Particles start out in a reasonable configuration but after just a few timesteps
the system "explodes" — particles fly off to infinity with insane velocities.

## Symptoms

- After 10 timesteps with dt=0.001, total energy should be roughly conserved
  (we expect < 1% drift for this integrator), but the reported energy error is
  enormous — sometimes hundreds of percent.
- With 256 particles in a stable cluster, max velocity after 10 steps should be
  in the single digits, but we're seeing velocities > 1000.
- It seems worse when particles are close together. A uniformly-spread
  configuration is *slightly* less broken.
- We added a softening parameter to prevent singularities, but particles still
  seem to get force spikes when they're near each other.

## What We've Tried

- Reduced timestep to dt=0.0001 — still explodes, just takes a few more steps.
- Increased softening epsilon from 0.01 to 1.0 — still wrong, forces are still
  spiking for close pairs.
- Checked that kernel launch dimensions are correct — they are.

## Expected Behavior

- Energy drift < 1% over 10 steps with dt=0.001 and epsilon=0.5.
- Max velocity stays bounded (< 20.0 for our test configuration).
- Force magnitudes should be smooth even for close particles.

## Environment

- CUDA Toolkit 12.x, any NVIDIA GPU with compute capability >= 3.5
