# Bug: RAII Resource Handle with Double-Free

## Description

A `FileHandle` RAII wrapper manages a "file descriptor" (simulated via a mock filesystem that tracks open/close counts). The class has a constructor and destructor, but is missing proper copy/move semantics:

1. **Missing copy constructor/assignment**: The compiler-generated copy constructor does a shallow copy of the file descriptor. When both the original and the copy are destroyed, the descriptor is closed twice (double-free).

2. **Missing move semantics**: There's no move constructor or move assignment, so returning a `FileHandle` from a function or inserting into a vector triggers copies (and thus double-frees).

The fix should:
- Delete the copy constructor and copy assignment operator (files shouldn't be silently copied).
- Add move constructor and move assignment operator that transfer ownership.

## Expected Behavior

- After copying is prevented and move semantics are added, open_count should always equal close_count at program end.
- A `FileHandle` can be returned from a factory function without double-free.
- `FileHandle` can be stored in a `std::vector` via move.

## Actual Behavior

- Copying a FileHandle leads to double-close (close_count > open_count).
- Program may crash or report mismatched open/close counts.

## Files

- `src/filehandle.h` — FileHandle RAII wrapper and MockFS
- `src/filehandle.cpp` — implementation
- `src/main.cpp` — test driver
