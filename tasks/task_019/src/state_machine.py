"""Generic state machine implementation."""


class InvalidTransitionError(Exception):
    """Raised when a transition is not valid from the current state."""
    pass


class Transition:
    """Represents a named transition between two states."""

    def __init__(self, name: str, source: str, target: str, guard=None):
        """
        Args:
            name: Transition name (e.g., "submit", "approve").
            source: The state this transition goes FROM.
            target: The state this transition goes TO.
            guard: Optional callable returning bool. Transition is only
                   allowed if guard returns True.
        """
        self.name = name
        self.source = source
        self.target = target
        self.guard = guard

    def __repr__(self):
        return f"Transition({self.name!r}: {self.source!r} -> {self.target!r})"


class StateMachine:
    """A generic finite state machine.

    States are strings. Transitions are registered with ``add_transition``
    and triggered by name with ``trigger``.
    """

    def __init__(self, initial_state: str):
        self._current_state = initial_state
        self._states = {initial_state}
        self._transitions = {}  # name -> Transition
        self._history = [initial_state]
        self._on_enter_callbacks = {}
        self._on_exit_callbacks = {}

    @property
    def state(self) -> str:
        """Return the current state."""
        return self._current_state

    @property
    def history(self) -> list:
        """Return the state transition history."""
        return list(self._history)

    def add_state(self, state: str) -> None:
        """Register a valid state."""
        self._states.add(state)

    def add_transition(self, name: str, source: str, target: str,
                       guard=None) -> None:
        """Register a named transition.

        Args:
            name: Unique name for this transition.
            source: Source state (must be registered).
            target: Target state (must be registered).
            guard: Optional guard callable.

        Raises:
            ValueError: If source or target state is not registered,
                       or if transition name already exists.
        """
        if source not in self._states:
            raise ValueError(f"Source state {source!r} not registered")
        if target not in self._states:
            raise ValueError(f"Target state {target!r} not registered")
        if name in self._transitions:
            raise ValueError(f"Transition {name!r} already exists")
        self._transitions[name] = Transition(name, source, target, guard)

    def trigger(self, transition_name: str, **context) -> str:
        """Trigger a named transition.

        Args:
            transition_name: The name of the transition to trigger.
            **context: Optional context passed to guard functions.

        Returns:
            The new state after the transition.

        Raises:
            InvalidTransitionError: If the transition is not valid.
        """
        if transition_name not in self._transitions:
            raise InvalidTransitionError(
                f"Unknown transition: {transition_name!r}"
            )

        transition = self._transitions[transition_name]

        # Check guard condition
        if transition.guard is not None:
            if not transition.guard(**context):
                raise InvalidTransitionError(
                    f"Guard condition failed for {transition_name!r}"
                )

        # Execute on_exit callback for current state
        if self._current_state in self._on_exit_callbacks:
            self._on_exit_callbacks[self._current_state]()

        # Perform the transition
        self._current_state = transition.target

        # Execute on_enter callback for new state
        if self._current_state in self._on_enter_callbacks:
            self._on_enter_callbacks[self._current_state]()

        self._history.append(self._current_state)
        return self._current_state

    def on_enter(self, state: str, callback) -> None:
        """Register a callback for entering a state."""
        self._on_enter_callbacks[state] = callback

    def on_exit(self, state: str, callback) -> None:
        """Register a callback for exiting a state."""
        self._on_exit_callbacks[state] = callback

    def get_available_transitions(self) -> list:
        """Return names of transitions available from the current state."""
        available = []
        for name, trans in self._transitions.items():
            if trans.source == self._current_state:
                available.append(name)
        return available

    def can_trigger(self, transition_name: str) -> bool:
        """Check if a transition can be triggered from the current state."""
        if transition_name not in self._transitions:
            return False
        trans = self._transitions[transition_name]
        return trans.source == self._current_state
