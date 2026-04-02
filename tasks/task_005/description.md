# Bug: deep_merge performs shallow update instead of recursive merge

## Description

The `deep_merge(base, override)` function is supposed to recursively merge two dictionaries. When both `base` and `override` have a nested dict at the same key, the function should merge them recursively. Instead, it does a shallow `dict.update()`, so nested dicts in `override` completely replace nested dicts in `base`, losing keys that only exist in `base`.

## Expected Behavior

```python
base     = {"a": {"x": 1, "y": 2}, "b": 10}
override = {"a": {"y": 3, "z": 4}}
result   = deep_merge(base, override)
# result == {"a": {"x": 1, "y": 3, "z": 4}, "b": 10}
```

Key `"x"` from `base["a"]` should be preserved.

## Actual Behavior

```python
# result == {"a": {"y": 3, "z": 4}, "b": 10}
```

`base["a"]` is completely replaced by `override["a"]`, losing `"x": 1`.

## How to Reproduce

```python
from config_merger import deep_merge

base = {"a": {"x": 1, "y": 2}}
override = {"a": {"y": 3}}
print(deep_merge(base, override))
# Expected: {"a": {"x": 1, "y": 3}}
# Actual:   {"a": {"y": 3}}
```
