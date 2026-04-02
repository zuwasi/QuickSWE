# Bug Report: Pipeline Produces Incorrect Results in Batched Mode

## Summary

We have a data processing pipeline that supports both eager and lazy (batched) evaluation modes. When running with batching enabled, the output data is incorrect — values appear to be corrupted or modified unexpectedly between pipeline stages.

## Steps to Reproduce

1. Create a pipeline with multiple stages (e.g., a filter followed by a map)
2. Enable batched mode with a batch size
3. Feed in a list of dictionary records
4. Observe that intermediate stage results are wrong — data appears to have been modified before the stage even processes it

## Expected Behavior

Each stage should receive the output of the previous stage, unmodified. A FilterStage followed by a MapStage should first filter, then map over the filtered results.

## Actual Behavior

When batching is enabled, data seems to get "ahead of itself" — stages receive data that has already been transformed by later stages. It's as if the stage boundaries are being ignored.

## Environment

- Python 3.10+
- No external dependencies

## Additional Notes

- The issue does NOT occur when batching is disabled (eager mode works perfectly)
- The serializer module was recently refactored and has some unusual type-checking logic — not sure if that's related
- The problem seems to get worse with more stages in the pipeline
- We've verified the individual stage implementations work correctly in isolation
