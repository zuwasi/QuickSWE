# Coroutine Scheduler – Incorrect Symmetric Transfer

## Problem

A cooperative task scheduler implements stackful coroutines using `setjmp`/`longjmp`
(simulated with explicit state machines for portability). Tasks can `yield()`,
`spawn()` new tasks, and `join()` on other tasks.

Users report:

1. After a task yields and is resumed, its local state is corrupted because the
   scheduler does not save/restore state correctly during the context switch.
2. `join()` on a completed task hangs instead of returning immediately.
3. The round-robin scheduler skips tasks: after yield, the next task in the
   queue is not the expected one because the current task is re-enqueued at
   the wrong position.

## Files

- `src/scheduler.hpp` — cooperative scheduler
- `src/main.cpp` — test driver
