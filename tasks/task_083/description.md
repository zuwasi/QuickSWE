# Bug Report: SpGEMM Output Has Extra Zeros and Wrong Values

## Summary

Our CUDA CSR × CSR sparse matrix multiplication produces incorrect results.
The output matrix contains extra zero entries and sometimes has completely
wrong values for certain matrix patterns.

## Symptoms

- Structured matrices (diagonal, banded) seem to work most of the time.
- Random sparse matrices with overlapping sparsity patterns produce wrong
  values — especially when multiple products contribute to the same output
  element.
- The output CSR has more non-zeros than the correct result. Many of the
  extra entries are zeros that shouldn't be in a sparse matrix.
- For matrices where products cancel out (e.g., A has +1 and -1 entries that
  combine to zero in C = A*B), the zero remains in the output instead of
  being eliminated.
- Some rows have duplicate column indices in the output, which is invalid CSR.

## What We've Tried

- Verified our CSR construction is correct by converting to dense and back.
- CPU reference multiplication produces correct results.
- The two-phase approach (count then fill) seems sound in principle but
  something is wrong in the counting and/or merging logic.

## Expected Behavior

- C = A * B should have no explicit zeros in CSR representation.
- No duplicate column indices per row.
- Values should match CPU dense multiplication within float tolerance.
- Output NNZ should equal the number of truly non-zero entries.

## Environment

- CUDA Toolkit 12.x, any NVIDIA GPU with compute capability >= 3.5
