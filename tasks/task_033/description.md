# Task 033: Varint Encoder Truncation Bug

## Problem

A Protocol Buffer-style varint encoder/decoder truncates values larger than
2^28 (268,435,456). The encoding loop terminates after 4 iterations (processing
only 7*4 = 28 bits) instead of continuing until all significant bits are
encoded. This causes large 32-bit and 64-bit values to be incorrectly encoded
and decoded.

## Expected Behavior

The varint encoder should handle values up to at least 2^64 - 1, producing
a variable-length encoding with 7 data bits per byte and a continuation bit.
The decoder should reconstruct the exact original value.

## Files

- `src/varint.py` — Varint encode/decode functions with message framing
