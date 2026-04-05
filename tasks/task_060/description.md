# Variadic Template – Incorrect Pack Expansion

## Problem

A utility header provides variadic template functions: `sum_all`, `all_of`,
`any_of`, `transform_reduce`, and `apply_to_each`. These use C++17 fold
expressions and parameter pack expansion.

Users report:

1. `sum_all(1, 2, 3)` works but `transform_reduce` with a lambda produces
   wrong results — the transformation is applied only to the first argument.
2. `apply_to_each` is supposed to call a function on every argument and collect
   results in a vector, but it only captures the last argument's result.
3. `all_of` and `any_of` work for 2 arguments but give wrong results for 3+
   arguments because the fold associativity is wrong.

## Files

- `src/variadic.hpp` — variadic template utilities
- `src/main.cpp` — test driver

## Expected Behaviour

- `sum_all(1,2,3)` → 6
- `transform_reduce([](auto x){ return x*x; }, 1, 2, 3)` → 14 (1+4+9)
- `apply_to_each([](auto x){ return x*2; }, 1, 2, 3)` → vector{2, 4, 6}
- `all_of(true, true, false)` → false
- `any_of(false, false, true)` → true
