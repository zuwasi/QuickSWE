# Lock-Free Stack – ABA Problem

## Problem

A lock-free stack implementation uses `std::atomic` and CAS (compare-and-swap)
for thread-safe push/pop. However, the implementation is susceptible to the ABA
problem and has additional bugs in its CAS logic.

Users report:

1. In single-threaded usage, after push-push-pop-push-pop-pop sequence, the
   wrong values are returned because the CAS loop does not properly reload the
   head pointer on failure.
2. The `pop()` function reads `next` from the node *after* the CAS, meaning
   another thread could have freed that node — but even in single-threaded mode,
   the stale read causes issues when nodes are reused.
3. The tagged pointer counter is not incremented on push, only on pop, causing
   the ABA protection to be incomplete.

## Files

- `src/lockfree_stack.hpp` — lock-free stack with tagged pointers
- `src/main.cpp` — single-threaded test driver exposing the bugs

## Expected Behaviour

- Push/pop must work correctly in LIFO order.
- The tagged pointer (counter) must be incremented on every CAS operation
  (both push and pop) to prevent ABA.
- The `next` pointer must be read *before* attempting CAS in pop.
