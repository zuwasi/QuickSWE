"""
Mergeable min-heap implementation supporting insert, extract_min,
merge, decrease_key, and bulk operations.
"""

from typing import List, Optional, Tuple, Any, Callable


class HeapEntry:
    """An entry in the heap with a priority key and associated value."""

    def __init__(self, key: float, value: Any = None):
        self.key = key
        self.value = value

    def __lt__(self, other):
        return self.key < other.key

    def __le__(self, other):
        return self.key <= other.key

    def __repr__(self):
        return f"HeapEntry({self.key}, {self.value!r})"


class MergeableHeap:
    """Min-heap that supports efficient merge operations."""

    def __init__(self):
        self._data: List[HeapEntry] = []

    @classmethod
    def from_list(cls, items: List[Tuple[float, Any]]) -> "MergeableHeap":
        heap = cls()
        heap._data = [HeapEntry(k, v) for k, v in items]
        heap._heapify()
        return heap

    def insert(self, key: float, value: Any = None):
        entry = HeapEntry(key, value)
        self._data.append(entry)
        self._sift_up(len(self._data) - 1)

    def peek_min(self) -> Optional[HeapEntry]:
        if not self._data:
            return None
        return self._data[0]

    def extract_min(self) -> Optional[HeapEntry]:
        if not self._data:
            return None
        if len(self._data) == 1:
            return self._data.pop()

        min_entry = self._data[0]
        self._data[0] = self._data.pop()
        self._sift_down(0)
        return min_entry

    def merge(self, other: "MergeableHeap") -> "MergeableHeap":
        result = MergeableHeap()
        result._data = self._data[:] + other._data[:]
        if result._data:
            result._heapify()
        return result

    def merge_inplace(self, other: "MergeableHeap"):
        self._data.extend(other._data)
        self._heapify()
        other._data = []

    def decrease_key(self, index: int, new_key: float):
        if index < 0 or index >= len(self._data):
            raise IndexError("Index out of range")
        if new_key > self._data[index].key:
            raise ValueError("New key is larger than current key")
        self._data[index].key = new_key
        self._sift_up(index)

    def delete(self, index: int) -> HeapEntry:
        if index < 0 or index >= len(self._data):
            raise IndexError("Index out of range")
        entry = self._data[index]
        self._data[index] = self._data[-1]
        self._data.pop()
        if index < len(self._data):
            self._sift_down(index)
            self._sift_up(index)
        return entry

    def size(self) -> int:
        return len(self._data)

    def is_empty(self) -> bool:
        return len(self._data) == 0

    def to_sorted_list(self) -> List[Tuple[float, Any]]:
        copy = MergeableHeap()
        copy._data = self._data[:]
        result = []
        while not copy.is_empty():
            entry = copy.extract_min()
            result.append((entry.key, entry.value))
        return result

    def _sift_up(self, index: int):
        while index > 0:
            parent = (index - 1) // 2
            if self._data[index] < self._data[parent]:
                self._data[index], self._data[parent] = (
                    self._data[parent], self._data[index])
                index = parent
            else:
                break

    def _sift_down(self, index: int):
        n = len(self._data)
        while True:
            smallest = index
            left = 2 * index + 1
            right = 2 * index + 2

            if left < n and self._data[left] < self._data[smallest]:
                smallest = left
            if right < n and self._data[right] < self._data[smallest]:
                smallest = right

            if smallest != index:
                self._data[index], self._data[smallest] = (
                    self._data[smallest], self._data[index])
                index = smallest
            else:
                break

    def _heapify(self):
        n = len(self._data)
        if n <= 1:
            return
        self._sift_down(0)

    def is_valid_heap(self) -> bool:
        n = len(self._data)
        for i in range(n):
            left = 2 * i + 1
            right = 2 * i + 2
            if left < n and self._data[i].key > self._data[left].key:
                return False
            if right < n and self._data[i].key > self._data[right].key:
                return False
        return True

    def get_keys(self) -> List[float]:
        return [e.key for e in self._data]


def merge_k_heaps(heaps: List[MergeableHeap]) -> MergeableHeap:
    """Merge k heaps into one."""
    if not heaps:
        return MergeableHeap()
    result = heaps[0]
    for i in range(1, len(heaps)):
        result = result.merge(heaps[i])
    return result


def k_way_merge_sorted(lists: List[List[int]]) -> List[int]:
    """Merge k sorted lists using a heap."""
    heap = MergeableHeap()
    for list_idx, lst in enumerate(lists):
        for val in lst:
            heap.insert(val, list_idx)

    result = []
    while not heap.is_empty():
        entry = heap.extract_min()
        result.append(int(entry.key))
    return result
