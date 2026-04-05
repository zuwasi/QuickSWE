# Circular Buffer – Incorrect Wrap-Around Logic

## Problem

A `CircularBuffer<T>` template class implements a fixed-size ring buffer supporting
`push_back`, `pop_front`, `front`, `back`, `full`, `empty`, and `size` operations.

Users report that:

1. After filling the buffer and then pushing additional elements (overwrite mode),
   the oldest elements are **not** correctly discarded — the buffer returns stale data.
2. The `size()` method returns wrong values once the internal indices wrap around.
3. Iterating the buffer after wrap-around yields elements in the wrong order.

## Files

- `src/circular_buffer.hpp` — the buffer implementation
- `src/main.cpp` — driver that runs selected test cases based on command-line args

## Expected Behaviour

- `push_back` on a full buffer should overwrite the oldest entry and advance the
  head pointer.
- `size()` must always return the correct number of valid elements (≤ capacity).
- Iteration from oldest to newest must respect insertion order after wrap-around.
