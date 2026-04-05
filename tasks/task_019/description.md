# Task 019 – Retry Decorator Doesn't Reset Attempt Counter

## Problem
The `retry` decorator wraps a function so that transient failures are
retried up to `max_retries` times with exponential backoff. The attempt
counter is stored in the closure and is **not** reset between independent
calls, so after the first failing invocation exhausts retries, subsequent
invocations immediately fail without retrying.

## Expected Behaviour
- Each call to the decorated function gets a fresh attempt counter.
- A failure in call #1 must not affect the retry budget of call #2.

## Files
- `src/retry.py` – the buggy decorator
- `tests/test_retry.py` – test suite
