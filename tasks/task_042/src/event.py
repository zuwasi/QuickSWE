"""
Event model for the calendar system.
Represents a scheduled event with start/end times and timezone.
"""

from datetime import datetime, timedelta, timezone


class Event:
    """A calendar event with start and end times.

    Events store timezone-aware datetimes. The timezone is preserved
    for display purposes.
    """

    _id_counter = 0

    def __init__(self, title, start, end, tz=None, description="",
                 attendees=None):
        """Initialize an event.

        Args:
            title: Event title.
            start: Start datetime (should be timezone-aware).
            end: End datetime (should be timezone-aware).
            tz: Optional timezone to apply if start/end are naive.
            description: Event description.
            attendees: List of attendee names.
        """
        Event._id_counter += 1
        self.id = Event._id_counter

        if tz and start.tzinfo is None:
            start = start.replace(tzinfo=tz)
        if tz and end.tzinfo is None:
            end = end.replace(tzinfo=tz)

        if start >= end:
            raise ValueError("Event start must be before end")

        self.title = title
        self.start = start
        self.end = end
        self.description = description
        self.attendees = attendees or []

    @property
    def duration(self):
        """Duration of the event."""
        return self.end - self.start

    @property
    def duration_minutes(self):
        """Duration in minutes."""
        return int(self.duration.total_seconds() / 60)

    @property
    def timezone_name(self):
        """String representation of the event's timezone."""
        if self.start.tzinfo:
            return str(self.start.tzinfo)
        return "naive"

    def overlaps_with(self, other):
        """Check if this event overlaps with another.

        BUG: Compares datetimes directly without normalizing to UTC.
        Python DOES compare tz-aware datetimes correctly when both have
        tzinfo, but this method is called from Calendar which strips
        tzinfo for comparison (see calendar.py).
        """
        return self.start < other.end and other.start < self.end

    def contains_time(self, dt):
        """Check if a datetime falls within this event."""
        return self.start <= dt < self.end

    def __repr__(self):
        return (
            f"Event({self.title!r}, "
            f"{self.start.strftime('%Y-%m-%d %H:%M %Z')} - "
            f"{self.end.strftime('%H:%M %Z')})"
        )

    def __eq__(self, other):
        if not isinstance(other, Event):
            return NotImplemented
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    @classmethod
    def reset_ids(cls):
        cls._id_counter = 0

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "description": self.description,
            "attendees": self.attendees,
        }
