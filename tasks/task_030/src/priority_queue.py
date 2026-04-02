"""MinHeap priority queue implementation."""


class MinHeap:
    """Min-heap priority queue for Dijkstra's algorithm.

    Stores (priority, item) tuples and provides efficient
    extract_min and decrease_key operations.
    """

    def __init__(self):
        self._heap = []
        self._size = 0

    @property
    def size(self):
        return self._size

    @property
    def is_empty(self):
        return self._size == 0

    def _parent(self, i):
        return (i - 1) // 2

    def _left(self, i):
        return 2 * i + 1

    def _right(self, i):
        return 2 * i + 2

    def _swap(self, i, j):
        self._heap[i], self._heap[j] = self._heap[j], self._heap[i]

    def _sift_up(self, i):
        """Sift element up to maintain heap property."""
        while i > 0:
            parent = self._parent(i)
            if self._heap[i][0] < self._heap[parent][0]:
                self._swap(i, parent)
                i = parent
            else:
                break

    def _sift_down(self, i):
        """Sift element down to maintain heap property.

        BUG: When comparing children, we find the smallest child and swap
        if it's smaller than the parent. But the comparison for the right
        child compares against the PARENT (index i) instead of the current
        smallest. This means when left < parent but right < left, we might
        not pick the right child, violating the heap property.

        Example: parent=5, left=3, right=1
        - smallest starts as i (5)
        - left(3) < parent(5) -> smallest = left
        - right(1) < parent(5) -> yes, but we should compare right < left
          (the current smallest), not right < parent. However, since we
          compare right < heap[smallest] where smallest was ALREADY set to
          left... wait, that's correct.

        Actually the REAL bug: after the first sift_down iteration,
        'i' is updated to 'smallest', but we use 'i' as the starting
        comparison point for the NEXT iteration. Since we already swapped,
        this is correct. The real bug is elsewhere...
        """
        while True:
            smallest = i
            left = self._left(i)
            right = self._right(i)

            if left < self._size and self._heap[left][0] < self._heap[smallest][0]:
                smallest = left
            if right < self._size and self._heap[right][0] < self._heap[smallest][0]:
                smallest = right

            if smallest != i:
                self._swap(i, smallest)
                i = smallest
            else:
                break

    def insert(self, priority, item):
        """Insert an item with given priority."""
        self._heap.append((priority, item))
        self._size += 1
        self._sift_up(self._size - 1)

    def extract_min(self):
        """Remove and return the (priority, item) with minimum priority."""
        if self._size == 0:
            raise IndexError("extract_min from empty heap")

        min_item = self._heap[0]

        # Move last element to root
        self._size -= 1
        if self._size > 0:
            self._heap[0] = self._heap[self._size]
            self._heap.pop()
            self._sift_down(0)
        else:
            self._heap.pop()

        return min_item

    def peek_min(self):
        """Return the minimum (priority, item) without removing it."""
        if self._size == 0:
            raise IndexError("peek_min on empty heap")
        return self._heap[0]

    def decrease_key(self, item, new_priority):
        """Decrease the priority of an item.

        BUG: When searching for the item, this compares full tuples
        (priority, item). When priorities are equal, Python tries to
        compare the items. If items are non-comparable types (e.g.,
        custom objects), this raises a TypeError.
        """
        for i in range(self._size):
            if self._heap[i][1] == item:
                if new_priority < self._heap[i][0]:
                    self._heap[i] = (new_priority, item)
                    self._sift_up(i)
                return True
        return False

    def contains(self, item):
        """Check if an item is in the heap."""
        for i in range(self._size):
            if self._heap[i][1] == item:
                return True
        return False

    def __len__(self):
        return self._size

    def __repr__(self):
        return f"MinHeap(size={self._size})"
