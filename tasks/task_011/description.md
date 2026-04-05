# Task 011 – Async Producer-Consumer Drops Messages

## Problem
The `AsyncBoundedQueue` class wraps `asyncio.Queue` with a bounded capacity.
When the queue is full, `put()` should wait (block asynchronously) until space
is available. Instead, it silently drops items that cannot be added immediately.

## Expected Behaviour
- `put(item)` must await until the item is successfully enqueued.
- No messages should be lost regardless of producer/consumer timing.
- `get()` must await until an item is available.

## Files
- `src/async_queue.py` – the buggy implementation
- `tests/test_async_queue.py` – test suite
