"""Tests for the calendar conflict detection and free slot finding."""

import sys
import os
import pytest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.event import Event
from src.scheduler import Scheduler
from src.calendar import Calendar


# Define timezone offsets for testing
UTC = timezone.utc
EST = timezone(timedelta(hours=-5))   # US Eastern Standard
PST = timezone(timedelta(hours=-8))   # US Pacific Standard
CST = timezone(timedelta(hours=-6))   # US Central Standard
IST = timezone(timedelta(hours=5, minutes=30))  # India Standard


@pytest.fixture(autouse=True)
def reset_event_ids():
    Event.reset_ids()
    yield


# ── pass-to-pass: these must always pass ─────────────────────────────────

class TestEventCreation:
    """Event creation and basic properties."""

    def test_event_creation(self):
        start = datetime(2025, 6, 15, 14, 0, tzinfo=UTC)
        end = datetime(2025, 6, 15, 15, 0, tzinfo=UTC)
        event = Event("Meeting", start, end)

        assert event.title == "Meeting"
        assert event.duration_minutes == 60
        assert event.start.tzinfo is not None

        with pytest.raises(ValueError):
            Event("Bad", end, start)  # start >= end

        event2 = Event(
            "Naive", 
            datetime(2025, 6, 15, 10, 0),
            datetime(2025, 6, 15, 11, 0),
            tz=EST,
        )
        assert event2.start.tzinfo == EST


class TestSchedulerAddEvents:
    """Scheduler add/remove/query operations."""

    def test_scheduler_add_events(self):
        scheduler = Scheduler()
        e1 = Event(
            "A",
            datetime(2025, 6, 15, 9, 0, tzinfo=UTC),
            datetime(2025, 6, 15, 10, 0, tzinfo=UTC),
        )
        e2 = Event(
            "B",
            datetime(2025, 6, 15, 11, 0, tzinfo=UTC),
            datetime(2025, 6, 15, 12, 0, tzinfo=UTC),
        )

        scheduler.add_event(e1)
        scheduler.add_event(e2)
        assert scheduler.event_count == 2

        retrieved = scheduler.get_event(e1.id)
        assert retrieved.title == "A"

        scheduler.remove_event(e1.id)
        assert scheduler.event_count == 1

        with pytest.raises(KeyError):
            scheduler.remove_event(999)


class TestConflictSameTimezone:
    """Conflict detection works within a single timezone."""

    def test_conflict_same_timezone(self):
        scheduler = Scheduler()
        cal = Calendar(scheduler)

        # Two overlapping events in UTC
        e1 = Event(
            "Meeting A",
            datetime(2025, 6, 15, 14, 0, tzinfo=UTC),
            datetime(2025, 6, 15, 15, 0, tzinfo=UTC),
        )
        e2 = Event(
            "Meeting B",
            datetime(2025, 6, 15, 14, 30, tzinfo=UTC),
            datetime(2025, 6, 15, 15, 30, tzinfo=UTC),
        )
        # Non-overlapping
        e3 = Event(
            "Meeting C",
            datetime(2025, 6, 15, 16, 0, tzinfo=UTC),
            datetime(2025, 6, 15, 17, 0, tzinfo=UTC),
        )

        scheduler.add_event(e1)
        scheduler.add_event(e2)
        scheduler.add_event(e3)

        conflicts = cal.find_conflicts()
        assert len(conflicts) == 1
        conflict_pair = conflicts[0]
        titles = {conflict_pair[0].title, conflict_pair[1].title}
        assert titles == {"Meeting A", "Meeting B"}


# ── fail-to-pass: these FAIL with the bug, PASS after fix ────────────────

class TestNoConflictDifferentTimezones:
    """Events in different timezones that don't actually overlap."""

    @pytest.mark.fail_to_pass
    def test_no_conflict_different_timezones(self):
        """2:00 PM EST and 2:00 PM PST are 3 hours apart.
        They should NOT conflict (assuming 1-hour meetings).

        BUG: Calendar._events_overlap strips tzinfo, so both are seen as
        "14:00" and reported as overlapping.
        """
        scheduler = Scheduler()
        cal = Calendar(scheduler)

        # 2:00 PM EST = 7:00 PM UTC
        e_east = Event(
            "East Coast Meeting",
            datetime(2025, 6, 15, 14, 0, tzinfo=EST),
            datetime(2025, 6, 15, 15, 0, tzinfo=EST),
        )
        # 2:00 PM PST = 10:00 PM UTC — 3 hours after the EST meeting
        e_west = Event(
            "West Coast Meeting",
            datetime(2025, 6, 15, 14, 0, tzinfo=PST),
            datetime(2025, 6, 15, 15, 0, tzinfo=PST),
        )

        scheduler.add_event(e_east)
        scheduler.add_event(e_west)

        conflicts = cal.find_conflicts()
        assert len(conflicts) == 0, (
            f"False conflict detected between events that are 3 hours apart: "
            f"{e_east} vs {e_west}"
        )


class TestFreeSlotsAcrossTimezones:
    """Free slot finding must respect timezone differences."""

    @pytest.mark.fail_to_pass
    def test_free_slots_across_timezones(self):
        """An event at 2:00 PM PST should block 5:00 PM EST, not 2:00 PM EST.

        BUG: find_free_slots strips timezone, misplacing events on the timeline.
        """
        scheduler = Scheduler()
        cal = Calendar(scheduler)

        # Event at 2:00 PM PST = 5:00 PM EST = 10:00 PM UTC
        pst_event = Event(
            "PST Meeting",
            datetime(2025, 6, 15, 14, 0, tzinfo=PST),
            datetime(2025, 6, 15, 15, 0, tzinfo=PST),  # 3-4 PM PST
        )
        scheduler.add_event(pst_event)

        # Query free slots in EST on that day
        from datetime import date
        free = cal.find_free_slots(
            date(2025, 6, 15), tz=EST, duration_minutes=30
        )

        # The PST event is 5:00-6:00 PM EST, so 2:00-3:00 PM EST should be free
        # BUG: with stripped timezone, 2pm PST is treated as 2pm EST,
        # incorrectly blocking 2-3 PM EST
        est_2pm = datetime(2025, 6, 15, 14, 0, tzinfo=EST)
        est_3pm = datetime(2025, 6, 15, 15, 0, tzinfo=EST)

        found_2pm_free = False
        for slot_start, slot_end in free:
            if slot_start <= est_2pm and slot_end >= est_3pm:
                found_2pm_free = True
                break

        assert found_2pm_free, (
            f"2:00-3:00 PM EST should be free (PST meeting is at 5-6 PM EST). "
            f"Free slots found: {free}"
        )


class TestConflictDetectionRealOverlap:
    """Events in different timezones that DO actually overlap."""

    @pytest.mark.fail_to_pass
    def test_conflict_detection_real_overlap(self):
        """10:00 AM EST and 7:00 AM PST both equal 3:00 PM UTC — they conflict.
        Meanwhile 6:00 PM IST = 12:30 PM UTC — no conflict.

        BUG: with stripped tz, 10am EST, 7am PST, and 6pm IST are all
        compared as their local hours (10, 7, 18) — getting wrong results.
        """
        scheduler = Scheduler()
        cal = Calendar(scheduler)

        # 10:00 AM EST = 3:00 PM UTC
        e1 = Event(
            "NY Standup",
            datetime(2025, 6, 15, 10, 0, tzinfo=EST),
            datetime(2025, 6, 15, 11, 0, tzinfo=EST),
        )
        # 7:00 AM PST = 3:00 PM UTC — SAME TIME, should conflict
        e2 = Event(
            "SF Standup",
            datetime(2025, 6, 15, 7, 0, tzinfo=PST),
            datetime(2025, 6, 15, 8, 0, tzinfo=PST),
        )
        # 6:00 PM IST = 12:30 PM UTC — NO conflict
        e3 = Event(
            "India Standup",
            datetime(2025, 6, 15, 18, 0, tzinfo=IST),
            datetime(2025, 6, 15, 19, 0, tzinfo=IST),
        )

        scheduler.add_event(e1)
        scheduler.add_event(e2)
        scheduler.add_event(e3)

        conflicts = cal.find_conflicts()

        # Should find exactly ONE conflict: e1 vs e2 (both at 3pm UTC)
        # e3 (12:30 UTC) should NOT conflict with either
        conflict_titles = set()
        for a, b in conflicts:
            conflict_titles.add(a.title)
            conflict_titles.add(b.title)

        assert "NY Standup" in conflict_titles, (
            "NY Standup and SF Standup should conflict (both at 3pm UTC)"
        )
        assert "SF Standup" in conflict_titles, (
            "NY Standup and SF Standup should conflict (both at 3pm UTC)"
        )

        assert len(conflicts) == 1, (
            f"Expected exactly 1 conflict (NY vs SF), got {len(conflicts)}: "
            f"{[(a.title, b.title) for a, b in conflicts]}"
        )
