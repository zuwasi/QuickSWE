"""
Stream processor that uses k-way merge to combine sorted streams.
Provides higher-level interface for processing merged data.
"""

from .sorted_iterator import SortedIterator
from .merge_iterator import MergeIterator


class StreamStats:
    """Statistics about a processed stream."""

    def __init__(self):
        self.total_items = 0
        self.unique_items = 0
        self.duplicate_items = 0
        self.min_value = None
        self.max_value = None
        self._last_value = None

    def record(self, value):
        """Record a value in the statistics."""
        self.total_items += 1
        if self.min_value is None or value < self.min_value:
            self.min_value = value
        if self.max_value is None or value > self.max_value:
            self.max_value = value
        if value == self._last_value:
            self.duplicate_items += 1
        else:
            self.unique_items += 1
        self._last_value = value

    def __repr__(self):
        return (
            f"StreamStats(total={self.total_items}, "
            f"unique={self.unique_items}, "
            f"dupes={self.duplicate_items})"
        )


class StreamProcessor:
    """Processes multiple sorted streams through a k-way merge.

    Provides methods for:
    - Merging sorted streams into a single sorted output
    - Deduplication of merged streams
    - Computing statistics on merged data
    """

    def __init__(self, streams=None):
        """Initialize with optional list of sorted data lists."""
        self._streams = []
        if streams:
            for s in streams:
                self.add_stream(s)

    def add_stream(self, data, source_name=None):
        """Add a sorted data stream."""
        if source_name is None:
            source_name = f"stream_{len(self._streams)}"
        if isinstance(data, SortedIterator):
            self._streams.append(data)
        else:
            self._streams.append(SortedIterator(list(data), source_name))

    def merge(self):
        """Merge all streams and return sorted output."""
        if not self._streams:
            return []
        merger = MergeIterator(self._streams)
        return merger.collect_all()

    def merge_unique(self):
        """Merge all streams and deduplicate."""
        if not self._streams:
            return []
        merger = MergeIterator(self._streams)
        result = []
        last = None
        while merger.has_next:
            value = merger.next()
            if value != last:
                result.append(value)
            last = value
        return result

    def merge_with_stats(self):
        """Merge all streams and compute statistics."""
        if not self._streams:
            return [], StreamStats()

        merger = MergeIterator(self._streams)
        stats = StreamStats()
        result = []

        while merger.has_next:
            value = merger.next()
            result.append(value)
            stats.record(value)

        return result, stats

    def verify_sorted(self, data):
        """Verify that a list is sorted."""
        for i in range(1, len(data)):
            if data[i] < data[i - 1]:
                return False, i
        return True, -1

    @property
    def stream_count(self):
        return len(self._streams)

    def __repr__(self):
        return f"StreamProcessor(streams={len(self._streams)})"
