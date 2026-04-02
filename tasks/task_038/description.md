# Bug Report: Merged Sorted Output Has Items Out of Order

## Summary
When processing multiple input files with similar data through the k-way merge pipeline, the merged output has items out of order. This happens intermittently and seems related to files containing overlapping value ranges.

## Steps to Reproduce
1. Create 3+ sorted input files with overlapping value ranges (e.g., [1,2,3,4], [1,2,3,5], [2,3,4,6])
2. Run the stream processor to merge them
3. Observe the output — values that appear in multiple files may be out of order

## Expected Behavior
Output should be perfectly sorted regardless of input overlap.

## Additional Notes
- Works fine when all input files have completely distinct values
- The min-heap implementation was hand-written — could be a comparator issue?
- Possibly related to Python's tuple comparison behavior
- We see TypeError exceptions occasionally but they seem intermittent
