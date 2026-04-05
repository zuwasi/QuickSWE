# Task 008: Run-Length Encoding Decoder Bug

## Problem

The `encode()` and `decode()` functions implement run-length encoding (RLE). The encoder works correctly, compressing strings like `"aaabbc"` into `"3a2b1c"`. However, the `decode()` function has a bug where it **drops the last character group** from the decoded output.

For example, decoding `"3a2b1c"` should produce `"aaabbc"` but instead produces `"aaabb"` (missing the final `"c"`).

## Expected Behavior

- `decode("3a2b1c")` → `"aaabbc"`
- `decode(encode(s)) == s` for any valid input string
- Single character strings should round-trip correctly
- The encoder should continue to work correctly

## Files

- `src/rle.py` — RLE encode and decode implementation
- `tests/test_rle.py` — Test suite
