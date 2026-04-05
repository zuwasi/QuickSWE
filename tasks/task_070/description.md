# Lock-Free Concurrent Hash Map – Incorrect Memory Ordering

## Problem

A concurrent hash map uses atomic operations for thread-safe access. It uses
separate chaining with atomic bucket heads. The memory ordering on atomic ops
is incorrect, causing visibility issues even in single-threaded test scenarios
due to compiler reordering.

Users report:

1. `insert` followed by `find` sometimes returns `nullopt` because the store
   to the bucket head uses `memory_order_relaxed`, which the compiler may
   reorder relative to the node initialization.
2. The size counter is incremented with `relaxed` ordering, causing `size()`
   to be inconsistent with actual contents.
3. `remove` marks a node as deleted but uses wrong ordering, so concurrent
   `find` still sees the deleted node.

## Files

- `src/concurrent_map.hpp` — lock-free hash map
- `src/main.cpp` — test driver
