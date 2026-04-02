# Feature Request: Add Retry Logic to HTTP Client

## Current State

The `SimpleHTTPClient` class in `src/http_client.py` has:
- `__init__(self)` — basic initialization
- `fetch(url)` — calls `self._do_request(url)` and returns the result
- `_do_request(url)` — a method that performs the actual request (designed to be overridden for testing)

Currently, if `_do_request` raises an exception, `fetch` immediately propagates it with no retry.

## Requested Feature

Add retry logic with exponential backoff:

1. Add `max_retries` parameter to `__init__(self, max_retries=3)` — the maximum number of retry attempts after the initial call fails (so total attempts = max_retries + 1)
2. Add `backoff_base` parameter to `__init__` with default `0.1` seconds
3. When `_do_request` raises an exception during `fetch`:
   - Retry up to `max_retries` times
   - Wait `backoff_base * (2 ** attempt_number)` seconds between retries (attempt 0, 1, 2...)
   - If all retries are exhausted, raise the last exception
4. Add a `call_count` property or attribute that tracks the total number of `_do_request` calls made during the last `fetch` call

## Acceptance Criteria

1. `fetch(url)` retries on failure up to `max_retries` times
2. Backoff timing follows exponential pattern
3. Successful retry returns the result normally
4. If all retries fail, the last exception is raised
5. `call_count` reflects the total attempts made in the last fetch
6. Existing behavior (successful fetch on first try) is unchanged
