# Bug Report: Cache computes values multiple times under load

## Summary

We have a caching layer (`CacheManager`) that wraps a thread-safe cache and provides a `get_or_compute(key, func)` method. The idea is that expensive computations are only run once per key — subsequent calls should return the cached result.

## Problem

Under concurrent access, the same expensive function is being called multiple times for the same key. Our logs show that when several threads request the same uncached key simultaneously, the computation runs 3-5 times instead of once. This wastes resources and, worse, sometimes returns stale/inconsistent results when the computation has side effects.

In single-threaded tests everything works fine. The issue only manifests under concurrent load.

## Steps to Reproduce

1. Create a `CacheManager` with a `ThreadSafeCache`
2. Define an expensive computation function
3. Launch 10+ threads all calling `get_or_compute` with the same key simultaneously
4. Observe that the computation function is invoked more than once

## Expected Behavior

The computation function should execute exactly once per key, regardless of how many threads request it concurrently.

## Environment

- Python 3.10+
- Threading-based concurrency
