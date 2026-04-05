# Custom Vector – Iterator Invalidation in Erase

## Problem

A `Vector<T>` class implements a dynamic array with iterators. The `erase()`
method removes elements and should return a valid iterator to the element
following the erased one.

Users report:

1. `erase(it)` returns an iterator pointing to the wrong element — elements
   after the erased position are shifted, but the returned iterator skips one.
2. `erase(first, last)` range erase corrupts the container when `first != last`.
   The shift count is calculated incorrectly.
3. After `erase()`, `size()` is decremented by the wrong amount for range erases.
4. Using the returned iterator to continue erasing in a loop (erase-remove
   idiom) skips elements.

## Files

- `src/vector.hpp` — Vector<T> with iterators and erase
- `src/main.cpp` — test driver

## Expected Behaviour

- `erase(it)` removes the element at `it` and returns iterator to the next element.
- `erase(first, last)` removes `[first, last)` and returns iterator to new position
  of the element that was at `last`.
- Size decrements correctly.
