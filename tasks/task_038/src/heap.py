"""
MinHeap implementation for the k-way merge.
Supports custom comparison through elements that support < operator.
"""


class MinHeap:
    """A min-heap (priority queue) implementation.

    Elements must support the < operator for comparison.
    Used internally by MergeIterator for k-way merge.
    """

    def __init__(self):
        self._data = []

    def push(self, item):
        """Add an item to the heap."""
        self._data.append(item)
        self._sift_up(len(self._data) - 1)

    def pop(self):
        """Remove and return the smallest item."""
        if not self._data:
            raise IndexError("pop from empty heap")
        if len(self._data) == 1:
            return self._data.pop()

        result = self._data[0]
        self._data[0] = self._data.pop()
        self._sift_down(0)
        return result

    def peek(self):
        """Return the smallest item without removing it."""
        if not self._data:
            raise IndexError("peek at empty heap")
        return self._data[0]

    def push_pop(self, item):
        """Push an item then pop the smallest. More efficient than push + pop."""
        if self._data and self._data[0] < item:
            result = self._data[0]
            self._data[0] = item
            self._sift_down(0)
            return result
        return item

    @property
    def size(self):
        return len(self._data)

    @property
    def is_empty(self):
        return len(self._data) == 0

    def _sift_up(self, index):
        """Move element up to maintain heap property."""
        while index > 0:
            parent = (index - 1) // 2
            if self._data[index] < self._data[parent]:
                self._data[index], self._data[parent] = (
                    self._data[parent],
                    self._data[index],
                )
                index = parent
            else:
                break

    def _sift_down(self, index):
        """Move element down to maintain heap property."""
        size = len(self._data)
        while True:
            smallest = index
            left = 2 * index + 1
            right = 2 * index + 2

            if left < size and self._data[left] < self._data[smallest]:
                smallest = left
            if right < size and self._data[right] < self._data[smallest]:
                smallest = right

            if smallest != index:
                self._data[index], self._data[smallest] = (
                    self._data[smallest],
                    self._data[index],
                )
                index = smallest
            else:
                break

    def __len__(self):
        return len(self._data)

    def __bool__(self):
        return len(self._data) > 0

    def __repr__(self):
        return f"MinHeap(size={len(self._data)})"

    def to_sorted_list(self):
        """Drain the heap into a sorted list (destructive)."""
        result = []
        while self._data:
            result.append(self.pop())
        return result
