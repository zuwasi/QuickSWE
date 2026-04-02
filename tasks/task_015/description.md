# Task 015: Simplify Nested Conditionals with Early Returns

## Current State

`src/permissions.py` has a `check_access(user, resource, action)` function that determines whether a user is allowed to perform an action on a resource. The logic is correct but implemented as a deeply nested if/else pyramid (5+ levels):

```
if user is active:
    if role is admin:
        ...
    else:
        if resource type is public:
            ...
        else:
            if user owns it:
                ...
            else:
                if action is read:
                    ...
                else:
                    ...
```

This "arrow anti-pattern" is extremely hard to read and modify.

## Code Smell

- **Arrow anti-pattern** / deeply nested conditionals.
- Difficult to trace which branch produces which result.

## Requested Refactoring

1. **Flatten `check_access`** using guard clauses and early returns. The logic must remain identical, but the nesting depth should be ≤ 2.
2. **Add `can_access(user, resource, action) -> bool`** — a convenience wrapper that returns `True` if `check_access` returns `"allow"`, `False` otherwise.

## Acceptance Criteria

- [ ] `can_access` is importable from `src.permissions` and returns a boolean.
- [ ] `check_access` produces the same result for every combination of inputs as the original.
- [ ] Maximum nesting depth in `check_access` is reduced to ≤ 2 levels.
