"""Utility functions for cache key generation and serialization."""

import hashlib
import json


def make_cache_key(*args, **kwargs):
    """Generate a deterministic cache key from arguments.

    Supports primitive types, lists, tuples, and dicts.
    """
    key_parts = []
    for arg in args:
        key_parts.append(_serialize(arg))
    for k in sorted(kwargs.keys()):
        key_parts.append(f"{k}={_serialize(kwargs[k])}")
    raw = "|".join(key_parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _serialize(obj):
    """Serialize an object to a string for cache key purposes."""
    if obj is None:
        return "None"
    if isinstance(obj, (int, float, str, bool)):
        return repr(obj)
    if isinstance(obj, (list, tuple)):
        return "[" + ",".join(_serialize(x) for x in obj) + "]"
    if isinstance(obj, dict):
        items = sorted(obj.items())
        return "{" + ",".join(f"{k}:{_serialize(v)}" for k, v in items) + "}"
    return str(obj)


def validate_ttl(ttl):
    """Validate a TTL value."""
    if ttl is None:
        return None
    if not isinstance(ttl, (int, float)):
        raise TypeError(f"TTL must be a number, got {type(ttl).__name__}")
    if ttl <= 0:
        raise ValueError(f"TTL must be positive, got {ttl}")
    return float(ttl)
