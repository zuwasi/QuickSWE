"""Observer pattern (EventEmitter) implementation."""

from typing import Any, Callable, Dict, List, Optional


class EventEmitter:
    """A simple event emitter supporting on, off, once, and emit."""

    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}
        self._once_wrappers: Dict[int, Callable] = {}
        self._emit_count: Dict[str, int] = {}

    def on(self, event: str, listener: Callable) -> "EventEmitter":
        """Register a listener for an event."""
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(listener)
        return self

    def off(self, event: str, listener: Callable) -> "EventEmitter":
        """Remove a listener for an event."""
        if event in self._listeners:
            original = self._once_wrappers.get(id(listener), listener)
            try:
                self._listeners[event].remove(original)
            except ValueError:
                try:
                    self._listeners[event].remove(listener)
                except ValueError:
                    pass
        return self

    def once(self, event: str, listener: Callable) -> "EventEmitter":
        """Register a listener that fires only once."""

        def wrapper(*args, **kwargs):
            self.off(event, wrapper)
            return listener(*args, **kwargs)

        self._once_wrappers[id(listener)] = wrapper
        return self.on(event, wrapper)

    def emit(self, event: str, *args: Any, **kwargs: Any) -> bool:
        """Emit an event, calling all registered listeners.

        Returns True if the event had listeners, False otherwise.
        """
        if event not in self._listeners:
            return False

        listeners = self._listeners[event]
        if not listeners:
            return False

        self._emit_count[event] = self._emit_count.get(event, 0) + 1

        for listener in listeners:
            listener(*args, **kwargs)

        return True

    def listener_count(self, event: str) -> int:
        """Return the number of listeners for an event."""
        return len(self._listeners.get(event, []))

    def event_names(self) -> list:
        """Return list of events that have listeners."""
        return [e for e, ls in self._listeners.items() if ls]

    def remove_all_listeners(self, event: Optional[str] = None) -> "EventEmitter":
        """Remove all listeners, optionally for a specific event."""
        if event is not None:
            self._listeners.pop(event, None)
        else:
            self._listeners.clear()
        return self

    def get_emit_count(self, event: str) -> int:
        """Return how many times an event has been emitted."""
        return self._emit_count.get(event, 0)


class TypedEventEmitter(EventEmitter):
    """An EventEmitter that validates event names against a schema."""

    def __init__(self, allowed_events: list):
        super().__init__()
        self._allowed = set(allowed_events)

    def _validate_event(self, event: str):
        if event not in self._allowed:
            raise ValueError(f"Unknown event: {event}")

    def on(self, event: str, listener: Callable) -> "TypedEventEmitter":
        self._validate_event(event)
        return super().on(event, listener)

    def emit(self, event: str, *args, **kwargs) -> bool:
        self._validate_event(event)
        return super().emit(event, *args, **kwargs)
