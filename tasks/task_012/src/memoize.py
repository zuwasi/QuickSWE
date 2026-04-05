"""Memoization decorator with support for arbitrary arguments."""

import functools
from typing import Any, Callable, Dict, Tuple


def _make_key(args: tuple, kwargs: dict) -> tuple:
    """Create a hashable cache key from function arguments.

    This must handle mutable arguments like lists and dicts by converting
    them to a frozen/hashable representation.
    """
    key_parts = []
    for arg in args:
        key_parts.append(id(arg))
    for k, v in sorted(kwargs.items()):
        key_parts.append((k, id(v)))
    return tuple(key_parts)


def memoize(func: Callable) -> Callable:
    """Decorator that caches function results based on arguments.

    Supports positional and keyword arguments, including mutable types
    like lists and dictionaries.
    """
    cache: Dict[tuple, Any] = {}
    call_count: Dict[str, int] = {"hits": 0, "misses": 0}

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        key = _make_key(args, kwargs)

        if key in cache:
            call_count["hits"] += 1
            return cache[key]

        call_count["misses"] += 1
        result = func(*args, **kwargs)
        cache[key] = result
        return result

    wrapper.cache = cache
    wrapper.call_count = call_count

    def cache_clear():
        cache.clear()
        call_count["hits"] = 0
        call_count["misses"] = 0

    def cache_info():
        return {
            "hits": call_count["hits"],
            "misses": call_count["misses"],
            "size": len(cache),
        }

    wrapper.cache_clear = cache_clear
    wrapper.cache_info = cache_info
    return wrapper


def memoize_with_ttl(ttl_seconds: float) -> Callable:
    """Decorator that caches results with a time-to-live expiration."""
    import time

    def decorator(func: Callable) -> Callable:
        cache: Dict[tuple, Tuple[Any, float]] = {}

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = _make_key(args, kwargs)
            now = time.time()

            if key in cache:
                result, timestamp = cache[key]
                if now - timestamp < ttl_seconds:
                    return result

            result = func(*args, **kwargs)
            cache[key] = (result, now)
            return result

        wrapper.cache = cache

        def cache_clear():
            cache.clear()

        wrapper.cache_clear = cache_clear
        return wrapper

    return decorator


class MemoizedProperty:
    """Descriptor that caches property results per instance."""

    def __init__(self, func):
        self.func = func
        self.attr_name = f"_memoized_{func.__name__}"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if not hasattr(obj, self.attr_name):
            setattr(obj, self.attr_name, self.func(obj))
        return getattr(obj, self.attr_name)

    def __set__(self, obj, value):
        raise AttributeError("Cannot set memoized property")

    def __delete__(self, obj):
        if hasattr(obj, self.attr_name):
            delattr(obj, self.attr_name)
