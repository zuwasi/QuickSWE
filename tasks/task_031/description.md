# Task 031: Reactive Data Binding System

## Overview

Complete a reactive data binding framework. The system has `ObservableValue` (wraps a value with change notification), `ComputedValue` (derives from observables), `Binding` (syncs two observables), and `Scope` (tracks dependencies automatically).

## Requirements

1. **Automatic dependency tracking**: When a `ComputedValue`'s compute function runs, any `ObservableValue.get()` calls during that execution should be automatically captured as dependencies. No manual `add_dependency()` calls.

2. **Computed recalculation**: When an `ObservableValue` changes, all `ComputedValue`s that depend on it must recompute automatically.

3. **Diamond dependency resolution**: If A feeds into B and C, and both B and C feed into D, then when A changes, D should only recompute **once**, not twice.

4. **Two-way binding**: `Binding` should sync two observables — when either changes, the other updates (with loop prevention).

5. **Lazy evaluation**: `ComputedValue` should only actually compute when its value is read (`.get()`), not eagerly on every dependency change. It should mark itself as "dirty" when a dependency changes.

6. **Error propagation**: If a compute function raises an exception, the `ComputedValue` should store the error and re-raise it on `.get()`.

7. **Batch updates**: `Scope.batch()` context manager should defer all recomputations until the batch exits.

## Existing Code

- `observable_value.py` has a working `ObservableValue` with `get()` and `set()`, but no dependency tracking integration.
- Other files have stubs/skeletons that need to be completed.

## Constraints

- Pure Python, no external dependencies.
- The API surface is defined by the tests — make them pass.
