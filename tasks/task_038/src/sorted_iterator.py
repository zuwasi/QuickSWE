"""
Sorted iterator wrapper for sorted data sources.
Provides a peek-able iterator interface over sorted data.
"""


class SortedIterator:
    """Wraps a sorted iterable with peek capability.

    Provides a standard interface for iterating over sorted data
    with the ability to peek at the next value without consuming it.
    """

    def __init__(self, data, source_name="unknown"):
        """Initialize with sorted data.

        Args:
            data: An iterable of sorted values.
            source_name: Identifier for the data source (for debugging).
        """
        if not isinstance(data, (list, tuple)):
            data = list(data)
        self._data = data
        self._index = 0
        self.source_name = source_name
        self._exhausted = False

    def peek(self):
        """Return the next value without consuming it.

        Returns None if exhausted.
        """
        if self._exhausted or self._index >= len(self._data):
            self._exhausted = True
            return None
        return self._data[self._index]

    def next(self):
        """Consume and return the next value.

        Returns None if exhausted.
        """
        if self._exhausted or self._index >= len(self._data):
            self._exhausted = True
            return None
        value = self._data[self._index]
        self._index += 1
        if self._index >= len(self._data):
            self._exhausted = True
        return value

    @property
    def has_next(self):
        """Check if there are more values."""
        return not self._exhausted and self._index < len(self._data)

    @property
    def consumed(self):
        """Number of values consumed so far."""
        return self._index

    @property
    def remaining(self):
        """Number of values remaining."""
        return max(0, len(self._data) - self._index)

    def reset(self):
        """Reset iterator to the beginning."""
        self._index = 0
        self._exhausted = False

    def __repr__(self):
        status = "exhausted" if self._exhausted else f"at {self._index}/{len(self._data)}"
        return f"SortedIterator({self.source_name!r}, {status})"

    def __len__(self):
        return len(self._data)

    def collect_remaining(self):
        """Collect all remaining values into a list."""
        result = []
        while self.has_next:
            result.append(self.next())
        return result

    @classmethod
    def from_range(cls, start, stop, step=1, source_name="range"):
        """Create a SortedIterator from a range."""
        return cls(list(range(start, stop, step)), source_name)

    @classmethod
    def empty(cls, source_name="empty"):
        """Create an empty SortedIterator."""
        return cls([], source_name)
