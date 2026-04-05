"""Finite state machine implementation."""

from typing import Any, Callable, Dict, List, Optional, Set, Tuple


class InvalidTransitionError(Exception):
    """Raised when a transition is not valid for the current state."""
    pass


class FiniteStateMachine:
    """A configurable finite state machine.

    Transitions are registered as (source_state, event) -> target_state.
    Optional callbacks can be attached to transitions.
    """

    def __init__(self, initial_state: str, states: Optional[Set[str]] = None):
        self._state = initial_state
        self._states: Set[str] = states or {initial_state}
        self._transitions: Dict[Tuple[str, str], str] = {}
        self._callbacks: Dict[Tuple[str, str], List[Callable]] = {}
        self._history: List[str] = [initial_state]
        self._on_enter: Dict[str, List[Callable]] = {}
        self._on_exit: Dict[str, List[Callable]] = {}

    @property
    def state(self) -> str:
        return self._state

    @property
    def history(self) -> List[str]:
        return list(self._history)

    def add_state(self, state: str) -> None:
        """Register a valid state."""
        self._states.add(state)

    def add_transition(self, source: str, event: str, target: str,
                       callback: Optional[Callable] = None) -> None:
        """Register a transition: source --event--> target."""
        self._states.add(source)
        self._states.add(target)
        self._transitions[(source, event)] = target
        if callback is not None:
            key = (source, event)
            if key not in self._callbacks:
                self._callbacks[key] = []
            self._callbacks[key].append(callback)

    def on_enter(self, state: str, callback: Callable) -> None:
        """Register a callback for entering a state."""
        if state not in self._on_enter:
            self._on_enter[state] = []
        self._on_enter[state].append(callback)

    def on_exit(self, state: str, callback: Callable) -> None:
        """Register a callback for exiting a state."""
        if state not in self._on_exit:
            self._on_exit[state] = []
        self._on_exit[state].append(callback)

    def trigger(self, event: str, **context: Any) -> str:
        """Trigger a transition by event name.

        Returns the new state after the transition.
        Raises InvalidTransitionError if the transition is not valid.
        """
        key = (self._state, event)

        target = self._transitions.get(key)

        if target is None:
            for (src, evt), tgt in self._transitions.items():
                if evt == event:
                    target = tgt
                    break

        old_state = self._state

        for cb in self._on_exit.get(old_state, []):
            cb(old_state, event, context)

        self._state = target
        self._history.append(self._state)

        for cb in self._callbacks.get((old_state, event), []):
            cb(old_state, target, context)

        for cb in self._on_enter.get(target, []):
            cb(target, event, context)

        return self._state

    def available_events(self) -> List[str]:
        """Return events available from the current state."""
        events = []
        for (src, evt) in self._transitions:
            if src == self._state:
                events.append(evt)
        return events

    def can_trigger(self, event: str) -> bool:
        """Check if an event can be triggered from the current state."""
        return (self._state, event) in self._transitions

    def reset(self) -> None:
        """Reset to the initial state."""
        initial = self._history[0]
        self._state = initial
        self._history = [initial]

    def get_all_transitions(self) -> Dict[Tuple[str, str], str]:
        """Return all registered transitions."""
        return dict(self._transitions)
