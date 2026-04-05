# SFINAE Type Dispatch – Fails for Const References

## Problem

A utility library uses SFINAE to dispatch different serialization strategies based
on type traits: arithmetic types get `to_string`, types with a `.serialize()`
method get custom handling, and everything else gets a fallback.

Users report:

1. Passing `const int&` or `const double&` to `serialize()` fails — it falls
   through to the fallback instead of matching the arithmetic overload.
2. Passing a `const` reference to a class with `.serialize()` method does not
   match the custom serialization overload.
3. The `has_serialize` trait gives incorrect results for reference-qualified types.

## Files

- `src/sfinae_dispatch.hpp` — type traits and dispatch functions
- `src/main.cpp` — test driver

## Expected Behaviour

- `serialize(42)`, `serialize(const_ref_to_int)`, and `serialize(3.14)` should
  all use the arithmetic path.
- `serialize(obj_with_serialize)` and `serialize(const_ref_to_obj)` should
  both call the custom `.serialize()` path.
- The SFINAE traits must strip reference and cv-qualifiers before checking.
