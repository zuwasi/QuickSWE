# Feature Request: Promise/Future-Based Async Task Runner

## Summary

We need a JavaScript-style Promise implementation in Python, backed by a thread-pool-based TaskExecutor. Promises should support `.then()`, `.catch()`, `.finally_()`, `Promise.all()`, and `Promise.race()`, with full error propagation through chains.

## Current State

- `src/promise.py`: Stub `Promise` class with `__init__`, `then`, `catch`, `finally_`, class methods `all`, `race`, `resolve`, `reject` — all raise `NotImplementedError`.
- `src/executor.py`: Partial `TaskExecutor` with a thread pool. Has `submit(fn, *args)` but returns raw `Future` instead of `Promise`.
- `src/chain.py`: Stub for `PromiseChain` helper to manage chained callbacks.
- `src/scheduler.py`: `WorkScheduler` that batches and schedules work items.

## Requirements

### Promise (`src/promise.py`)
1. `Promise(executor_fn)` — takes `executor_fn(resolve, reject)`, calls it immediately.
2. `.then(on_fulfilled, on_rejected=None)` — returns new Promise. If current resolves, calls `on_fulfilled` with value. If current rejects, calls `on_rejected` with reason (or propagates rejection).
3. `.catch(on_rejected)` — shorthand for `.then(None, on_rejected)`.
4. `.finally_(on_settled)` — called whether resolved or rejected. Returns Promise that preserves original result.
5. `Promise.resolve(value)` — returns immediately resolved Promise.
6. `Promise.reject(reason)` — returns immediately rejected Promise.
7. `Promise.all(promises)` — resolves when all resolve (list of values), rejects if any rejects.
8. `Promise.race(promises)` — resolves/rejects with first settled promise's result.

### Chain (`src/chain.py`)
- Helper for managing ordered callback chains with error propagation.

### Executor Integration (`src/executor.py`)
- `TaskExecutor.submit()` should return a `Promise` instead of raw Future.

## Key Behaviors
- Chaining: `promise.then(f1).then(f2).catch(handler)` — if `f1` raises, skip `f2`, run `handler`.
- Error propagation: Unhandled rejection propagates through chain until caught.
- `Promise.all` short-circuits on first rejection.
- `Promise.race` settles with whichever promise settles first.
- Thread safety: Promises must be safe to resolve/reject from any thread.
