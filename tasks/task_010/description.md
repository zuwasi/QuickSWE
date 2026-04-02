# Feature Request: Add Rate Limiting to API Client

## Current State

The `APIClient` class in `src/api_client.py` has:
- `__init__(self)` — basic initialization
- `call(endpoint)` — calls `self._execute(endpoint)` and returns the result
- `_execute(endpoint)` — performs the API call (designed to be overridden)

Currently there is no rate limiting — calls happen as fast as they are made.

## Requested Feature

Add rate limiting so that the client enforces a maximum number of calls per second.

1. Add `max_calls_per_second` parameter to `__init__(self, max_calls_per_second=10)`
2. Track call timestamps in a sliding window
3. If a `call()` would exceed the rate limit, it should **block (sleep)** until the rate limit window allows it
4. The rate limiter should use a 1-second sliding window

## Acceptance Criteria

1. `APIClient(max_calls_per_second=5)` allows at most 5 calls per second
2. When rate limit is exceeded, `call()` blocks until a slot is available
3. Basic `call()` still works and returns results from `_execute()`
4. Rapid successive calls beyond the limit take at least the expected time
5. Default rate limit is 10 calls per second
