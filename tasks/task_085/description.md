# Bug Report: Radix Sort Wrong Order for Signed Integers

## Summary

Our CUDA radix sort works correctly for unsigned (positive) integers but
produces wrong ordering when the input contains negative numbers. All
negative values end up after the positive values instead of before them.

## Symptoms

- Arrays of all-positive integers sort correctly.
- Mixed positive/negative arrays produce: [positive sorted...] [negative sorted...]
  instead of [negative sorted...] [positive sorted...].
- The sign bit (bit 31) is treated as a regular bit, so all negative
  numbers (sign bit = 1) sort after all positive numbers (sign bit = 0).
- Need to flip the sign bit before sorting and flip it back after, so
  that negative numbers (originally 1xxx) become 0xxx and sort first.

## Expected Behavior

- Signed integers should sort in correct ascending order:
  -100, -50, -1, 0, 1, 50, 100
- Must handle mixed positive/negative inputs.

## Build Notes

Compile with: `nvcc -rdc=true -lcudadevrt -lm`
