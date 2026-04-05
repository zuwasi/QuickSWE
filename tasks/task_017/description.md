# Task 017 – Expression Evaluator Ignores Operator Precedence

## Problem
The `evaluate()` function parses and evaluates arithmetic expressions.
It currently evaluates operators strictly left-to-right, so `3 + 4 * 2`
returns 14 instead of the correct 11.

## Expected Behaviour
- Multiplication and division bind tighter than addition and subtraction.
- Parenthesised sub-expressions are evaluated first.
- `evaluate("3+4*2")` → 11, not 14.

## Files
- `src/evaluator.py` – the buggy evaluator
- `tests/test_evaluator.py` – test suite
