# Mini Garbage Collector – Mark-Compact with Incorrect Forwarding Pointers

## Problem

A mark-compact garbage collector manages a heap of objects. Each object has an
ID, a set of references to other objects, and a forwarding pointer used during
compaction. The collector supports `allocate`, `add_reference`, `collect`,
and `compact`.

Users report:

1. After compaction, references between objects point to stale (pre-compaction)
   locations — the forwarding pointer update phase does not fix references
   inside live objects.
2. Objects reachable only through a chain (A→B→C) are incorrectly collected
   because the mark phase does not propagate transitively.
3. After multiple collect/compact cycles, `dereference(id)` returns data from
   the wrong object.

## Files

- `src/gc.hpp` — mark-compact garbage collector
- `src/main.cpp` — test driver
