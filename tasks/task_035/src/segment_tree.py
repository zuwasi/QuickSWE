"""
Segment tree with lazy propagation for range sum queries and range updates.

Supports:
- Point update
- Range update (add a value to all elements in [l, r])
- Range query (sum of elements in [l, r])
- Point query
"""

from typing import List, Optional, Callable


class SegmentTree:
    """Segment tree supporting range updates and range queries with lazy propagation."""

    def __init__(self, data: List[int]):
        self.n = len(data)
        if self.n == 0:
            self._tree = []
            self._lazy = []
            return
        self._tree = [0] * (4 * self.n)
        self._lazy = [0] * (4 * self.n)
        self._build(data, 1, 0, self.n - 1)

    def _build(self, data: List[int], node: int, start: int, end: int):
        if start == end:
            self._tree[node] = data[start]
            return
        mid = (start + end) // 2
        self._build(data, 2 * node, start, mid)
        self._build(data, 2 * node + 1, mid + 1, end)
        self._tree[node] = self._tree[2 * node] + self._tree[2 * node + 1]

    def _push_down(self, node: int, start: int, end: int):
        if self._lazy[node] != 0:
            mid = (start + end) // 2
            left_count = mid - start + 1
            right_count = end - mid

            self._tree[2 * node] += self._lazy[node] * left_count
            self._lazy[2 * node] += self._lazy[node]

            self._tree[2 * node + 1] += self._lazy[node] * right_count
            self._lazy[2 * node + 1] += self._lazy[node]

            self._lazy[node] = 0

    def range_update(self, l: int, r: int, val: int):
        """Add val to every element in [l, r]."""
        self._range_update(1, 0, self.n - 1, l, r, val)

    def _range_update(self, node: int, start: int, end: int,
                      l: int, r: int, val: int):
        if r < start or end < l:
            return
        if l <= start and end <= r:
            self._tree[node] += val * (end - start + 1)
            self._lazy[node] += val
            return
        self._push_down(node, start, end)
        mid = (start + end) // 2
        self._range_update(2 * node, start, mid, l, r, val)
        self._range_update(2 * node + 1, mid + 1, end, l, r, val)
        self._tree[node] = self._tree[2 * node] + self._tree[2 * node + 1]

    def range_query(self, l: int, r: int) -> int:
        """Return sum of elements in [l, r]."""
        return self._range_query(1, 0, self.n - 1, l, r)

    def _range_query(self, node: int, start: int, end: int,
                     l: int, r: int) -> int:
        if r < start or end < l:
            return 0
        if l <= start and end <= r:
            return self._tree[node]
        mid = (start + end) // 2
        left_sum = self._range_query(2 * node, start, mid, l, r)
        right_sum = self._range_query(2 * node + 1, mid + 1, end, l, r)
        return left_sum + right_sum

    def point_update(self, index: int, val: int):
        """Set element at index to val."""
        self._point_update(1, 0, self.n - 1, index, val)

    def _point_update(self, node: int, start: int, end: int,
                      index: int, val: int):
        if start == end:
            self._tree[node] = val
            return
        self._push_down(node, start, end)
        mid = (start + end) // 2
        if index <= mid:
            self._point_update(2 * node, start, mid, index, val)
        else:
            self._point_update(2 * node + 1, mid + 1, end, index, val)
        self._tree[node] = self._tree[2 * node] + self._tree[2 * node + 1]

    def point_query(self, index: int) -> int:
        """Return the value at index."""
        return self._point_query(1, 0, self.n - 1, index)

    def _point_query(self, node: int, start: int, end: int,
                     index: int) -> int:
        if start == end:
            return self._tree[node]
        self._push_down(node, start, end)
        mid = (start + end) // 2
        if index <= mid:
            return self._point_query(2 * node, start, mid, index)
        else:
            return self._point_query(2 * node + 1, mid + 1, end, index)

    def get_all(self) -> List[int]:
        """Return all elements."""
        return [self.point_query(i) for i in range(self.n)]


class MinSegmentTree:
    """Segment tree for range minimum queries with lazy propagation."""

    def __init__(self, data: List[int]):
        self.n = len(data)
        if self.n == 0:
            self._tree = []
            self._lazy = []
            return
        self._tree = [0] * (4 * self.n)
        self._lazy = [0] * (4 * self.n)
        self._build(data, 1, 0, self.n - 1)

    def _build(self, data: List[int], node: int, start: int, end: int):
        if start == end:
            self._tree[node] = data[start]
            return
        mid = (start + end) // 2
        self._build(data, 2 * node, start, mid)
        self._build(data, 2 * node + 1, mid + 1, end)
        self._tree[node] = min(self._tree[2 * node], self._tree[2 * node + 1])

    def _push_down(self, node: int):
        if self._lazy[node] != 0:
            for child in [2 * node, 2 * node + 1]:
                self._tree[child] += self._lazy[node]
                self._lazy[child] += self._lazy[node]
            self._lazy[node] = 0

    def range_update(self, l: int, r: int, val: int):
        self._range_update(1, 0, self.n - 1, l, r, val)

    def _range_update(self, node: int, start: int, end: int,
                      l: int, r: int, val: int):
        if r < start or end < l:
            return
        if l <= start and end <= r:
            self._tree[node] += val
            self._lazy[node] += val
            return
        self._push_down(node)
        mid = (start + end) // 2
        self._range_update(2 * node, start, mid, l, r, val)
        self._range_update(2 * node + 1, mid + 1, end, l, r, val)
        self._tree[node] = min(self._tree[2 * node], self._tree[2 * node + 1])

    def range_min(self, l: int, r: int) -> int:
        return self._range_min(1, 0, self.n - 1, l, r)

    def _range_min(self, node: int, start: int, end: int,
                   l: int, r: int) -> int:
        if r < start or end < l:
            return float('inf')
        if l <= start and end <= r:
            return self._tree[node]
        self._push_down(node)
        mid = (start + end) // 2
        return min(
            self._range_min(2 * node, start, mid, l, r),
            self._range_min(2 * node + 1, mid + 1, end, l, r),
        )
