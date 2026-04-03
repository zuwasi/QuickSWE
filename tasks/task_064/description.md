# Bug: Smart Pointer Use-After-Move in C++

## Description

A `ResourceManager` class manages resources using `std::unique_ptr`. It has a method `transferResource()` that moves a `unique_ptr` into a `shared_ptr` parameter of a helper function. After the `std::move`, the code continues to use the moved-from `unique_ptr`, which is now null, causing a null pointer dereference.

Additionally, the `cloneResource()` method attempts to copy a `unique_ptr` (which is non-copyable) by working around it incorrectly — it manually creates a raw pointer copy but doesn't properly manage ownership, leading to a use-after-free scenario.

## Expected Behavior

- `transferResource()` should safely transfer ownership and not use the pointer afterward, or should use `shared_ptr` from the start.
- `cloneResource()` should create an independent deep copy of the resource.
- `getResourceInfo()` should return resource info without crashing.

## Actual Behavior

- `transferResource()` crashes with null pointer dereference after the move.
- Resource access after transfer crashes.

## Files

- `src/resource_manager.h` — Resource and ResourceManager declarations
- `src/resource_manager.cpp` — implementation with use-after-move bug
- `src/main.cpp` — test driver
