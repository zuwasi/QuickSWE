"""Core event bus for publish/subscribe communication."""

from dataclasses import dataclass, field
from typing import Callable, Any
import time


@dataclass
class Event:
    """Represents a domain event."""
    event_type: str
    payload: dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    source: str = ""


class EventBus:
    """Publish/subscribe event bus.

    Supports subscribing handlers to event types and publishing events
    to all registered handlers for that type.
    """

    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = {}
        self._event_log: list[Event] = []
        self._max_log_size = 1000

    def subscribe(self, event_type: str, handler: Callable) -> None:
        """Register a handler for an event type.

        Args:
            event_type: The type of event to subscribe to.
            handler: Callable that takes an Event and an EventBus reference.
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        if handler not in self._subscribers[event_type]:
            self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: Callable) -> bool:
        """Remove a handler for an event type."""
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(handler)
                return True
            except ValueError:
                return False
        return False

    def publish(self, event: Event) -> list[Any]:
        """Publish an event to all subscribed handlers.

        Args:
            event: The event to publish.

        Returns:
            List of results from all handlers.
        """
        self._log_event(event)
        results = []
        handlers = self._subscribers.get(event.event_type, [])
        for handler in handlers:
            result = handler(event, self)
            results.append(result)
        return results

    def get_subscriber_count(self, event_type: str) -> int:
        """Return the number of subscribers for an event type."""
        return len(self._subscribers.get(event_type, []))

    def get_event_log(self) -> list[Event]:
        """Return the event log."""
        return list(self._event_log)

    def clear_log(self) -> None:
        """Clear the event log."""
        self._event_log.clear()

    def _log_event(self, event: Event) -> None:
        """Log an event, evicting oldest if at capacity."""
        self._event_log.append(event)
        if len(self._event_log) > self._max_log_size:
            self._event_log = self._event_log[-self._max_log_size:]
