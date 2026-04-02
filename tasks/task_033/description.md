# Task 033: Convert Synchronous I/O Pipeline to Async with Backpressure

## Overview

Refactor a synchronous read→process→write pipeline into an async system using asyncio. Add backpressure so that fast producers don't overwhelm slow consumers.

## Requirements

1. **Async conversion**: Reader, Processor, and Writer must have async methods (`async def read_chunk()`, `async def process_chunk()`, `async def write_chunk()`).

2. **Backpressure via bounded queues**: Pipeline uses `asyncio.Queue(maxsize=N)` between stages. If the queue is full, the upstream stage blocks until space is available.

3. **BufferPool with semaphore**: `BufferPool` manages a fixed number of reusable `bytearray` buffers. Uses `asyncio.Semaphore` to limit concurrent checkouts. `async def acquire()` and `release()`.

4. **Concurrent pipeline**: `Pipeline.run()` launches Reader, Processor, and Writer as concurrent `asyncio.Task`s. Reader reads chunks and puts them on the read_queue. Processor takes from read_queue, processes, puts on write_queue. Writer takes from write_queue and writes.

5. **Graceful shutdown**: Reader sends a sentinel (None) when done. Each stage propagates the sentinel downstream and exits.

6. **Metrics**: `MetricsCollector` records throughput (chunks/sec), total bytes, and latency per chunk. Must be thread-safe for concurrent access.

7. **Backward compatibility**: The sync interfaces of Reader/Processor/Writer should still work (pass-to-pass tests check these).

## Existing Code

- All files have working synchronous implementations.
- The refactoring adds async versions alongside (or replacing) the sync code.

## Constraints

- Pure Python, use only `asyncio` from stdlib.
- No external async libraries.
