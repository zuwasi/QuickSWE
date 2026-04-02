"""Validation utilities for workflow state machines."""

from .state_machine import StateMachine


def validate_workflow(sm: StateMachine, expected_transitions: dict) -> list:
    """Validate that a state machine's transitions match expectations.

    Args:
        sm: The state machine to validate.
        expected_transitions: Dict mapping transition name to (source, target).

    Returns:
        List of validation error strings (empty if valid).
    """
    errors = []
    for name, (expected_source, expected_target) in expected_transitions.items():
        if name not in sm._transitions:
            errors.append(f"Missing transition: {name}")
            continue
        trans = sm._transitions[name]
        if trans.source != expected_source:
            errors.append(
                f"Transition {name}: expected source {expected_source!r}, "
                f"got {trans.source!r}"
            )
        if trans.target != expected_target:
            errors.append(
                f"Transition {name}: expected target {expected_target!r}, "
                f"got {trans.target!r}"
            )
    return errors


def get_reachable_states(sm: StateMachine, from_state: str) -> set:
    """Find all states reachable from a given state via any transitions."""
    reachable = set()
    _explore(sm, from_state, reachable)
    return reachable


def _explore(sm, state, visited):
    if state in visited:
        return
    visited.add(state)
    for trans in sm._transitions.values():
        if trans.source == state:
            _explore(sm, trans.target, visited)
