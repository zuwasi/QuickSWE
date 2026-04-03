# Bug: Template Metaprogramming Type Traits Bug

## Description

A custom type traits library provides `my_is_same`, `my_is_pointer`, `my_is_const`, and `my_remove_const`. The `my_is_pointer` trait has a partial specialization for `T*`, but does NOT have a specialization for `const T*`. This means `my_is_pointer<const int*>::value` is `false` when it should be `true`.

Additionally, `my_remove_const` is missing a specialization for `const volatile T`, so it doesn't strip `const` from `const volatile` qualified types.

The tests use `static_assert` at compile time — if the traits are wrong, the program fails to compile. The test driver prints "PASS" for each trait group if compilation succeeds.

## Expected Behavior

- `my_is_pointer<int* const>::value` should be `true` (const pointer to int is still a pointer).
- `my_is_pointer<int* volatile>::value` should be `true`.
- `my_remove_const<const volatile int>::type` should be `volatile int`.
- `my_remove_pointer<int* const>::type` should be `int`.
- All static_asserts pass, program compiles and prints results.

## Actual Behavior

- Compilation fails because `my_is_pointer<int* const>` resolves to `false` (the `T*` specialization doesn't match cv-qualified pointer types like `int* const`).
- `my_remove_const<const volatile int>` doesn't strip const.
- `my_remove_pointer<int* const>` doesn't strip the pointer.

## Files

- `src/type_traits.h` — custom type traits with bugs
- `src/main.cpp` — test driver with static_asserts
