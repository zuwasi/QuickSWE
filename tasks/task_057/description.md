# Shared Pointer Clone – Incorrect Reference Counting

## Problem

A `SharedPtr<T>` class mimics `std::shared_ptr` with manual reference counting.
It supports construction, copy construction, copy assignment, move operations,
`reset()`, `get()`, `use_count()`, and `operator*`/`operator->`.

Users report:

1. Self-assignment (`a = a`) causes a use-after-free / double-free crash.
2. After copy-assigning from one SharedPtr to another, the old resource is leaked
   (ref count of the old pointee is not decremented).
3. After a chain of assignments, `use_count()` returns incorrect values.

## Files

- `src/shared_ptr.hpp` — SharedPtr implementation
- `src/main.cpp` — test driver

## Expected Behaviour

- Copy assignment must decrement the old ref count (freeing if it drops to zero)
  and increment the new ref count.
- Self-assignment must be a no-op.
- `use_count()` must always reflect the exact number of SharedPtr instances
  sharing ownership.
