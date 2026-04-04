# Bug Report: FFT Forward-Inverse Roundtrip Fails

## Summary

Our CUDA Cooley-Tukey FFT implementation doesn't reconstruct the original signal
when doing forward FFT followed by inverse FFT. The error is not just floating
point noise — it's completely wrong.

## Symptoms

- Forward FFT of a known signal (e.g., single sine wave) produces plausible-
  looking frequency domain output, but the magnitudes aren't quite right.
- Inverse FFT of the forward result does NOT match the original signal.
  Reconstruction error is huge (> 0.1 RMS per element).
- The error seems to get **worse** for larger input sizes. N=16 is kinda close,
  N=256 is clearly wrong, N=1024 is garbage.
- For N=8 it almost works but some elements are swapped.

## What We've Tried

- Verified the CPU reference FFT gives correct roundtrip — it does.
- Checked kernel launch dimensions — they look correct.
- Printed twiddle factors — they look like valid unit-circle values but we're
  not sure the signs are right for inverse vs forward.

## Expected Behavior

- `IFFT(FFT(x))` should reconstruct `x` with RMS error < 1e-5 for float.
- FFT of a pure sine wave at frequency k should produce a spike at bin k.
- Should work for all power-of-2 sizes from 8 to 4096.

## Environment

- CUDA Toolkit 12.x, any NVIDIA GPU with compute capability >= 3.5
