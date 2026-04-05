# Bug Report: Multi-Stream Pipeline Produces Partial Results

## Summary

Our multi-stream pipeline processes data in 3 stages: transform, reduce,
and normalize. Each stage runs in its own stream. The pipeline produces
incorrect results because stage dependencies are not properly enforced.

## Symptoms

- Stage 2 (reduce) reads data before stage 1 (transform) finishes writing it.
- Stage 3 (normalize) reads the reduction result before stage 2 completes.
- The event recording and stream wait calls are either missing or applied
  to the wrong streams.
- `cudaEventRecord` records on the default stream instead of the
  producing stream, so the event fires immediately.
- `cudaStreamWaitEvent` is called on the producing stream instead of
  the consuming stream, providing no synchronization benefit.
- Results are correct only when N is very small (single-launch).

## Expected Behavior

- All pipeline stages execute in correct dependency order.
- Output should match sequential CPU processing.

## Build Notes

Compile with: `nvcc -rdc=true -lcudadevrt -lm`
