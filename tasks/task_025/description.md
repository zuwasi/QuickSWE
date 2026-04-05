# Task 025: Schema Validator Covariant Type Bug

## Problem

A schema type validator rejects valid covariant types inside container types.
When validating that `List[Dog]` is compatible with an expected type of
`List[Animal]` (where Dog is a subclass of Animal), the validator performs an
exact type match on the inner type parameter instead of a covariant (subtype)
check, causing validation to fail incorrectly.

## Expected Behavior

The validator should accept any subtype in covariant positions:
- `Dog` should be valid where `Animal` is expected
- `List[Dog]` should be valid where `List[Animal]` is expected
- `Dict[str, Dog]` should be valid where `Dict[str, Animal]` is expected

## Files

- `src/type_validator.py` — Type schema validator with container support
