# Task 046: Type Inference Occurs Check Missing

## Description

A Hindley-Milner type inference engine with type variables, function types, and
constructed types (like List, Option) implements a unification algorithm. The
unification is missing the "occurs check" — it doesn't verify that a type variable
doesn't appear in the type it's being unified with.

## Bug

When unifying a type variable `t` with a type that contains `t` (e.g., `List[t]`),
the algorithm should fail with an "infinite type" error. Without the occurs check,
it succeeds, creating a recursive/infinite type that causes infinite recursion when
the type is later traversed.

## Expected Behavior

Unification should perform an occurs check: before binding type variable `t` to
type `T`, verify that `t` does not appear free in `T`. If it does, raise an error.
