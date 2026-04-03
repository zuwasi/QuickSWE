# Bug: Circular Buffer with Wrap-around Bug

## Description

A ring buffer (circular buffer) implementation for integers. The write operation correctly wraps `write_pos` using modulo arithmetic. However, the read operation has a bug: it uses a simple `read_pos < write_pos` check to determine if data is available. After the write pointer wraps around (so `write_pos < read_pos`), the `cb_read` function incorrectly thinks the buffer is empty and returns -1, even though there are unread items.

The correct approach is to track the count of items in the buffer, or use a separate `full` flag, rather than comparing raw positions.

## Expected Behavior

- After writing 6 items into a buffer of capacity 4 (with reads interleaved), all written items should be readable in FIFO order.
- The `cb_count` function should accurately report the number of unread items at all times.

## Actual Behavior

- After the write pointer wraps, reads fail (return -1) even though data exists.
- `cb_count` returns a negative value or zero when the buffer contains items after wrap.

## Files

- `src/circbuf.h` — circular buffer struct and API
- `src/circbuf.c` — implementation with the wrap-around bug
- `src/main.c` — test driver
