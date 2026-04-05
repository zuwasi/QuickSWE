"""
Interval Tree with merge overlapping functionality.

Supports inserting intervals, querying for intervals that contain a point,
and merging all overlapping intervals into a minimal set.
"""


class Interval:
    """Represents a closed interval [start, end]."""

    def __init__(self, start, end):
        if start > end:
            raise ValueError(f"Invalid interval: start ({start}) > end ({end})")
        self.start = start
        self.end = end

    def __repr__(self):
        return f"Interval({self.start}, {self.end})"

    def __eq__(self, other):
        if not isinstance(other, Interval):
            return NotImplemented
        return self.start == other.start and self.end == other.end

    def __hash__(self):
        return hash((self.start, self.end))

    def overlaps(self, other):
        """Check if this interval overlaps with another.

        Two intervals overlap if they share any point in common.
        Touching intervals (e.g., [1,3] and [3,5]) should be considered
        overlapping since they share the boundary point.
        """
        return self.start < other.end and other.start < self.end

    def merge(self, other):
        """Merge this interval with another, returning the union."""
        if not self.overlaps(other):
            raise ValueError(f"Cannot merge non-overlapping intervals: {self}, {other}")
        return Interval(min(self.start, other.start), max(self.end, other.end))

    def contains_point(self, point):
        """Check if this interval contains a given point."""
        return self.start <= point <= self.end


class IntervalTree:
    """A collection of intervals supporting queries and merging."""

    def __init__(self):
        self._intervals = []

    def insert(self, start, end):
        """Insert a new interval [start, end]."""
        interval = Interval(start, end)
        self._intervals.append(interval)

    def query(self, point):
        """Return all intervals containing the given point."""
        return [iv for iv in self._intervals if iv.contains_point(point)]

    def query_range(self, start, end):
        """Return all intervals that overlap with [start, end]."""
        query_iv = Interval(start, end)
        return [iv for iv in self._intervals if iv.overlaps(query_iv)]

    @property
    def intervals(self):
        """Return a copy of the current intervals list."""
        return list(self._intervals)

    @property
    def size(self):
        """Return the number of intervals stored."""
        return len(self._intervals)

    def merge_overlapping(self):
        """Merge all overlapping intervals and return the merged list.

        This modifies the internal state to contain only the merged intervals.
        Intervals are sorted by start time, then merged greedily.

        Returns:
            list[Interval]: The merged intervals.
        """
        if not self._intervals:
            return []

        sorted_intervals = sorted(self._intervals, key=lambda iv: (iv.start, iv.end))
        merged = [Interval(sorted_intervals[0].start, sorted_intervals[0].end)]

        for current in sorted_intervals[1:]:
            last = merged[-1]
            if current.start < last.end:
                merged[-1] = Interval(last.start, max(last.end, current.end))
            else:
                merged.append(Interval(current.start, current.end))

        self._intervals = merged
        return list(merged)

    def remove(self, start, end):
        """Remove an interval matching [start, end] exactly."""
        target = Interval(start, end)
        self._intervals = [iv for iv in self._intervals if iv != target]

    def clear(self):
        """Remove all intervals."""
        self._intervals = []

    def __len__(self):
        return len(self._intervals)

    def __repr__(self):
        return f"IntervalTree({self._intervals})"
