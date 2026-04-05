import os
import sys
import pytest
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.cron_parser import CronExpression


# ──────────────────────────────────────────────
# pass_to_pass: these must always pass
# ──────────────────────────────────────────────


class TestCronBasics:
    """Tests for cron parsing that don't involve day-of-week."""

    def test_parse_every_minute(self):
        cron = CronExpression("* * * * *")
        assert cron.minutes == list(range(60))

    def test_specific_time(self):
        cron = CronExpression("30 9 * * *")
        assert cron.minutes == [30]
        assert cron.hours == [9]

    def test_next_run_specific_hour_minute(self):
        """Next run for '0 12 * * *' after 2026-01-01 10:00 should be 12:00 same day."""
        cron = CronExpression("0 12 * * *")
        after = datetime(2026, 1, 1, 10, 0, 0)
        result = cron.next_run(after)
        assert result.hour == 12
        assert result.minute == 0
        assert result.day == 1


# ──────────────────────────────────────────────
# fail_to_pass: these fail before the fix
# ──────────────────────────────────────────────


class TestCronDayOfWeek:
    """Tests for day-of-week — uses wrong mapping (0=Monday instead of 0=Sunday)."""

    @pytest.mark.fail_to_pass
    def test_sunday_is_zero(self):
        """'0 9 * * 0' means every Sunday at 9:00 in standard cron."""
        cron = CronExpression("0 9 * * 0")
        # 2026-04-05 is a Sunday
        after = datetime(2026, 4, 4, 10, 0, 0)  # Saturday
        result = cron.next_run(after)
        assert result.weekday() == 6, (
            f"Expected Sunday (weekday=6), got weekday={result.weekday()} "
            f"({result.strftime('%A %Y-%m-%d %H:%M')})"
        )
        assert result.day == 5  # April 5, 2026 is Sunday

    @pytest.mark.fail_to_pass
    def test_friday_is_five(self):
        """'0 18 * * 5' means every Friday at 18:00."""
        cron = CronExpression("0 18 * * 5")
        # 2026-04-06 is Monday
        after = datetime(2026, 4, 6, 0, 0, 0)
        result = cron.next_run(after)
        assert result.weekday() == 4, (
            f"Expected Friday (weekday=4), got weekday={result.weekday()} "
            f"({result.strftime('%A %Y-%m-%d %H:%M')})"
        )
        assert result.day == 10  # April 10, 2026 is Friday

    @pytest.mark.fail_to_pass
    def test_weekday_range_mon_to_fri(self):
        """'0 9 * * 1-5' means Monday through Friday."""
        cron = CronExpression("0 9 * * 1-5")
        # 2026-04-04 is Saturday
        after = datetime(2026, 4, 4, 10, 0, 0)
        result = cron.next_run(after)
        # Should be Monday April 6
        assert result.weekday() == 0, (
            f"Expected Monday (weekday=0), got weekday={result.weekday()} "
            f"({result.strftime('%A %Y-%m-%d %H:%M')})"
        )
        assert result.day == 6
