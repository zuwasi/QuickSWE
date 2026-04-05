# Task 013 – Observer Pattern Skips Listeners on Removal During Emit

## Problem
The `EventEmitter` class implements the observer pattern. When a listener
removes itself (or another listener) during `emit()`, the iteration over
the listener list is corrupted — subsequent listeners in the list are
skipped because the list mutates under the iterator.

## Expected Behaviour
- `emit()` must notify every listener that was registered at the moment
  `emit()` was called, even if a listener removes itself during the callback.
- Listeners added during `emit()` should NOT fire in that same emit cycle.

## Files
- `src/observer.py` – the buggy implementation
- `tests/test_observer.py` – test suite
