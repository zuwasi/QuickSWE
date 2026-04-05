# Task 003: Rate Limiter Token Bucket Overflow

## Problem

The `TokenBucket` rate limiter allows consuming more tokens than the bucket's maximum capacity after a refill period. The `refill()` method adds tokens based on elapsed time, but never caps the token count at the maximum capacity, leading to unbounded token accumulation.

## Expected Behavior

- After initialization, tokens should equal the capacity
- After refilling, tokens should never exceed capacity
- `consume(n)` should return `True` only if there are enough tokens
- Even after a long idle period, the bucket should never have more tokens than its capacity

## Files

- `src/rate_limiter.py` — TokenBucket implementation
- `tests/test_rate_limiter.py` — Test suite
