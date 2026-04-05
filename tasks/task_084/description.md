# Bug Report: Stream Compaction Duplicates/Drops Elements

## Summary

Our CUDA stream compaction (select elements > threshold) produces output
with duplicated elements and missing others. The count of selected
elements is also wrong.

## Symptoms

- The output count doesn't match the CPU reference count.
- Some elements appear twice in the output while others are missing.
- The prefix sum (exclusive scan) used for scatter indices is computed
  as an inclusive scan instead, causing each thread to write to the
  wrong output position (off by one).
- The predicate evaluation and the scan use different flag arrays,
  meaning the scatter position doesn't correspond to the actual
  predicate result.

## Expected Behavior

- Output should contain exactly those elements where `data[i] > threshold`.
- Output count should match CPU reference count.
- No duplicates, no missing elements.

## Build Notes

Compile with: `nvcc -rdc=true -lcudadevrt -lm`
