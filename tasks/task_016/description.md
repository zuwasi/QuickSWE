# Task 016 – FSM Accepts Invalid Transitions

## Problem
The `FiniteStateMachine` class models state transitions. The `trigger()`
method should only allow transitions that have been explicitly registered
via `add_transition()`. Instead, it blindly sets the state to whatever
target is requested without validating the transition is defined for the
current state.

## Expected Behaviour
- `trigger(event)` must raise `InvalidTransitionError` if no transition is
  defined from the current state for the given event.
- The state must remain unchanged after a rejected transition.
- Valid transitions work as before.

## Files
- `src/fsm.py` – the buggy FSM
- `tests/test_fsm.py` – test suite
