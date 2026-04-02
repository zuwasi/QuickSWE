"""
Event scheduler for managing calendar events.
Provides add, remove, and query operations.
"""

from datetime import datetime, timezone, timedelta
from .event import Event


class Scheduler:
    """Manages a collection of calendar events.

    Stores events and provides query methods. Does NOT handle
    conflict detection — that's in Calendar.
    """

    def __init__(self, name="default"):
        self.name = name
        self._events = {}
        self._categories = {}  # Red herring — not related to the bug

    def add_event(self, event):
        """Add an event to the scheduler."""
        if not isinstance(event, Event):
            raise TypeError("Expected an Event instance")
        self._events[event.id] = event
        return event.id

    def remove_event(self, event_id):
        """Remove an event by ID."""
        if event_id not in self._events:
            raise KeyError(f"Event {event_id} not found")
        del self._events[event_id]

    def get_event(self, event_id):
        """Get an event by ID."""
        return self._events.get(event_id)

    def get_events(self, start=None, end=None):
        """Get events, optionally filtered by date range."""
        events = list(self._events.values())
        if start:
            events = [e for e in events if e.end > start]
        if end:
            events = [e for e in events if e.start < end]
        return sorted(events, key=lambda e: e.start)

    def get_events_on_date(self, date):
        """Get all events on a specific date.

        Note: compares date portion only, using the event's own timezone.
        """
        result = []
        for event in self._events.values():
            if event.start.date() == date or event.end.date() == date:
                result.append(event)
        return sorted(result, key=lambda e: e.start)

    @property
    def event_count(self):
        return len(self._events)

    def all_events(self):
        return sorted(self._events.values(), key=lambda e: e.start)

    def clear(self):
        self._events.clear()

    def __repr__(self):
        return f"Scheduler({self.name!r}, events={self.event_count})"
