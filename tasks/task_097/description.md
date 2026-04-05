# Bug Report: GPU FFT Produces Wrong Frequency Domain Results

## Summary

Our CUDA Cooley-Tukey FFT implementation produces incorrect frequency
domain results. The bit-reversal permutation and twiddle factor
computation both have bugs.

## Symptoms

- DC component (index 0) is correct but all other bins are wrong.
- The bit-reversal permutation uses `log2(N) - 1` bits instead of
  `log2(N)` bits, causing incorrect index mapping.
- The twiddle factor angle has the wrong sign — uses positive angle
  for forward FFT instead of negative (should be `e^{-j2πk/N}`).
- The butterfly operation indexes the partner element with an
  off-by-one: uses `idx + half` where `half` is computed as
  `stride` instead of `stride/2`.
- Inverse FFT produces wrong scaling (divides by N/2 instead of N).

## Expected Behavior

- Forward FFT should match CPU DFT reference within floating-point tolerance.
- Inverse FFT applied to forward FFT should recover original signal.

## Build Notes

Compile with: `nvcc -rdc=true -lcudadevrt -lm`
