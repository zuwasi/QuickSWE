"""
Calendar module for conflict detection and free slot finding.
Works with the Scheduler to analyze event overlaps.
"""

from datetime import datetime, timedelta, timezone
from .event import Event


class Calendar:
    """Analyzes events for conflicts and free time.

    Uses the Scheduler's event list to find overlaps and free slots.
    """

    def __init__(self, scheduler):
        self._scheduler = scheduler

    def find_conflicts(self, events=None):
        """Find all pairs of events that overlap.

        BUG: Normalizes datetimes by stripping timezone info and comparing
        the raw hour/minute values. This means 2:00 PM EST and 2:00 PM PST
        appear to be at the same time, when they're actually 3 hours apart.

        Returns list of (event_a, event_b) tuples.
        """
        if events is None:
            events = self._scheduler.all_events()

        conflicts = []
        for i in range(len(events)):
            for j in range(i + 1, len(events)):
                if self._events_overlap(events[i], events[j]):
                    conflicts.append((events[i], events[j]))
        return conflicts

    def _events_overlap(self, event_a, event_b):
        """Check if two events overlap.

        BUG: Strips tzinfo and compares naive datetimes.
        This treats 2:00 PM in ANY timezone as the same moment.
        """
        # BUG: .replace(tzinfo=None) strips the timezone, making
        # "2pm EST" and "2pm PST" look identical
        a_start = event_a.start.replace(tzinfo=None)
        a_end = event_a.end.replace(tzinfo=None)
        b_start = event_b.start.replace(tzinfo=None)
        b_end = event_b.end.replace(tzinfo=None)

        return a_start < b_end and b_start < a_end

    def find_free_slots(self, date, tz, duration_minutes=30):
        """Find free time slots on a given date.

        BUG: Same timezone comparison issue — events in different
        timezones are placed at wrong positions on the timeline.

        Args:
            date: The date to check.
            tz: Timezone for the query (working hours context).
            duration_minutes: Minimum slot duration in minutes.

        Returns:
            List of (start, end) datetime tuples representing free slots.
        """
        day_start = datetime(date.year, date.month, date.day, 8, 0, tzinfo=tz)
        day_end = datetime(date.year, date.month, date.day, 18, 0, tzinfo=tz)

        events = self._scheduler.all_events()

        # BUG: Filter and sort events by stripping timezone
        day_events = []
        for event in events:
            # BUG: strip tz before comparing — wrong!
            evt_start = event.start.replace(tzinfo=None)
            evt_end = event.end.replace(tzinfo=None)
            ds_naive = day_start.replace(tzinfo=None)
            de_naive = day_end.replace(tzinfo=None)

            if evt_start < de_naive and evt_end > ds_naive:
                day_events.append(event)

        # Sort by start time (BUG: stripped timezone)
        day_events.sort(key=lambda e: e.start.replace(tzinfo=None))

        free_slots = []
        current = day_start
        min_duration = timedelta(minutes=duration_minutes)

        for event in day_events:
            # BUG: compare with stripped tz
            evt_start_naive = event.start.replace(tzinfo=None)
            current_naive = current.replace(tzinfo=None)

            if evt_start_naive > current_naive:
                slot_end = event.start.replace(tzinfo=tz)
                if (slot_end - current) >= min_duration:
                    free_slots.append((current, slot_end))

            evt_end_with_tz = event.end.replace(tzinfo=tz)
            if evt_end_with_tz > current:
                current = evt_end_with_tz

        if (day_end - current) >= min_duration:
            free_slots.append((current, day_end))

        return free_slots

    def has_conflicts(self, events=None):
        """Check if any conflicts exist."""
        return len(self.find_conflicts(events)) > 0

    def get_busiest_day(self, start_date, end_date, tz):
        """Find the day with the most events in a date range."""
        day_counts = {}
        current = start_date
        while current <= end_date:
            events = self._scheduler.get_events_on_date(current)
            day_counts[current] = len(events)
            current += timedelta(days=1)

        if not day_counts:
            return None
        return max(day_counts, key=day_counts.get)

    def __repr__(self):
        return f"Calendar(events={self._scheduler.event_count})"
