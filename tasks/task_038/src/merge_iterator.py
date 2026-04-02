"""
K-way merge iterator using a min-heap.
Merges multiple sorted iterators into a single sorted stream.
"""

from .heap import MinHeap
from .sorted_iterator import SortedIterator


class MergeIterator:
    """Merges multiple SortedIterators into one sorted output.

    Uses a MinHeap to efficiently pick the smallest value
    across all input iterators at each step.
    """

    def __init__(self, iterators):
        """Initialize with a list of SortedIterators.

        Args:
            iterators: List of SortedIterator instances, each yielding
                       sorted values.
        """
        self._iterators = list(iterators)
        self._heap = MinHeap()
        self._exhausted = False
        self._total_emitted = 0

        # Seed the heap with the first element from each iterator
        # BUG: heap entries are (value, iterator) tuples.
        # When two values are equal, Python falls back to comparing
        # the second tuple element (the SortedIterator). SortedIterator
        # doesn't implement __lt__, so this raises TypeError or gives
        # non-deterministic ordering depending on Python version.
        for it in self._iterators:
            if it.has_next:
                value = it.next()
                self._heap.push((value, it))

    def next(self):
        """Return the next value in merged sorted order.

        Returns None if all iterators are exhausted.
        """
        if self._heap.is_empty:
            self._exhausted = True
            return None

        value, source_it = self._heap.pop()

        # If this iterator has more values, push the next one
        if source_it.has_next:
            next_val = source_it.next()
            self._heap.push((next_val, source_it))

        self._total_emitted += 1
        return value

    @property
    def has_next(self):
        """Check if there are more values to emit."""
        return not self._heap.is_empty

    def collect_all(self):
        """Collect all remaining values into a list."""
        result = []
        while self.has_next:
            result.append(self.next())
        return result

    @property
    def total_emitted(self):
        return self._total_emitted

    def __repr__(self):
        return (
            f"MergeIterator(sources={len(self._iterators)}, "
            f"heap_size={self._heap.size}, emitted={self._total_emitted})"
        )

    @classmethod
    def from_lists(cls, *lists, source_prefix="list"):
        """Create a MergeIterator from multiple sorted lists."""
        iterators = [
            SortedIterator(lst, source_name=f"{source_prefix}_{i}")
            for i, lst in enumerate(lists)
        ]
        return cls(iterators)

    @classmethod
    def merge_two(cls, iter_a, iter_b):
        """Convenience method to merge exactly two iterators."""
        return cls([iter_a, iter_b])
