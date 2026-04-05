"""
Cron Expression Parser.

Parses standard 5-field cron expressions and computes the next
scheduled run time from a given reference time.

Fields: minute hour day-of-month month day-of-week
  - minute:       0-59
  - hour:         0-23
  - day-of-month: 1-31
  - month:        1-12
  - day-of-week:  0-6 (standard cron: 0=Sunday, 6=Saturday)

Supports: specific values, ranges (1-5), lists (1,3,5), steps (*/2), wildcard (*)
"""

from datetime import datetime, timedelta


def _parse_field(field, min_val, max_val):
    """Parse a single cron field into a set of valid values.

    Args:
        field: The cron field string (e.g., "*/5", "1-3", "1,2,3", "*").
        min_val: Minimum valid value for this field.
        max_val: Maximum valid value for this field.

    Returns:
        A sorted list of valid integer values.

    Raises:
        ValueError: If the field is malformed.
    """
    values = set()

    for part in field.split(","):
        if "/" in part:
            range_part, step = part.split("/", 1)
            step = int(step)
            if range_part == "*":
                start, end = min_val, max_val
            elif "-" in range_part:
                start, end = map(int, range_part.split("-", 1))
            else:
                start = int(range_part)
                end = max_val
            for v in range(start, end + 1, step):
                if min_val <= v <= max_val:
                    values.add(v)
        elif "-" in part:
            start, end = map(int, part.split("-", 1))
            for v in range(start, end + 1):
                if min_val <= v <= max_val:
                    values.add(v)
        elif part == "*":
            values.update(range(min_val, max_val + 1))
        else:
            v = int(part)
            if min_val <= v <= max_val:
                values.add(v)
            else:
                raise ValueError(
                    f"Value {v} out of range [{min_val}, {max_val}]"
                )

    return sorted(values)


class CronExpression:
    """Parses and evaluates a 5-field cron expression."""

    def __init__(self, expression):
        """Parse a cron expression string.

        Args:
            expression: A 5-field cron expression string.

        Raises:
            ValueError: If the expression is malformed.
        """
        fields = expression.strip().split()
        if len(fields) != 5:
            raise ValueError(
                f"Expected 5 fields, got {len(fields)}: '{expression}'"
            )

        self._expression = expression
        self._minutes = _parse_field(fields[0], 0, 59)
        self._hours = _parse_field(fields[1], 0, 23)
        self._days_of_month = _parse_field(fields[2], 1, 31)
        self._months = _parse_field(fields[3], 1, 12)
        self._days_of_week = _parse_field(fields[4], 0, 6)

    @property
    def expression(self):
        return self._expression

    @property
    def minutes(self):
        return list(self._minutes)

    @property
    def hours(self):
        return list(self._hours)

    @property
    def days_of_month(self):
        return list(self._days_of_month)

    @property
    def months(self):
        return list(self._months)

    @property
    def days_of_week(self):
        return list(self._days_of_week)

    def _matches(self, dt):
        """Check if a datetime matches this cron expression.

        Args:
            dt: A datetime object.

        Returns:
            True if the datetime matches all cron fields.
        """
        if dt.minute not in self._minutes:
            return False
        if dt.hour not in self._hours:
            return False
        if dt.day not in self._days_of_month:
            return False
        if dt.month not in self._months:
            return False

        # Python's isoweekday(): Monday=1, Sunday=7
        # Convert to cron day-of-week
        # Using Monday=0 mapping (this is the internal representation)
        dow = dt.isoweekday() - 1  # Monday=0, Tuesday=1, ..., Sunday=6
        if dow not in self._days_of_week:
            return False

        return True

    def next_run(self, after=None):
        """Compute the next time this cron expression fires.

        Searches minute-by-minute starting from the reference time.
        Limited to searching 366 days ahead.

        Args:
            after: Reference datetime. Defaults to now.

        Returns:
            The next datetime matching the cron expression.

        Raises:
            RuntimeError: If no match is found within 366 days.
        """
        if after is None:
            after = datetime.now()

        # Start from the next minute
        candidate = after.replace(second=0, microsecond=0) + timedelta(minutes=1)
        max_time = after + timedelta(days=366)

        while candidate <= max_time:
            if self._matches(candidate):
                return candidate

            # Skip ahead intelligently
            if candidate.month not in self._months:
                # Jump to next valid month
                if candidate.month == 12:
                    candidate = candidate.replace(
                        year=candidate.year + 1, month=self._months[0],
                        day=1, hour=0, minute=0
                    )
                else:
                    next_months = [m for m in self._months if m > candidate.month]
                    if next_months:
                        candidate = candidate.replace(
                            month=next_months[0], day=1, hour=0, minute=0
                        )
                    else:
                        candidate = candidate.replace(
                            year=candidate.year + 1, month=self._months[0],
                            day=1, hour=0, minute=0
                        )
                continue

            candidate += timedelta(minutes=1)

        raise RuntimeError(
            f"No matching time found within 366 days for: {self._expression}"
        )

    def __repr__(self):
        return f"CronExpression('{self._expression}')"
