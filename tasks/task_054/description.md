# Priority Queue (Min-Heap) – Incorrect Sift-Down

## Problem

A `MinHeap<T>` template class implements a binary min-heap with `push`, `pop`,
`top`, `size`, and `empty` operations.

Users report:

1. After pushing elements in descending order and then popping, elements do not
   come out in ascending order.
2. Extracting the minimum after several insertions sometimes returns a non-minimum
   element.
3. Heap-sorting by repeated `pop()` produces an unsorted sequence for inputs larger
   than 3 elements.

## Files

- `src/min_heap.hpp` — MinHeap implementation
- `src/main.cpp` — driver program

## Expected Behaviour

- `top()` always returns the smallest element currently in the heap.
- Successive `pop()` calls yield elements in non-decreasing order.
- The heap property is maintained after every insert and extract operation.
