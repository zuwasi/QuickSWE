# Pratt Parser – Incorrect Precedence Binding

## Problem

A Pratt (top-down operator precedence) parser evaluates arithmetic expressions
with `+`, `-`, `*`, `/`, `^` (power), and parentheses.

Users report:

1. `2 + 3 * 4` evaluates to 20 instead of 14 — multiplication does not bind
   tighter than addition.
2. `2 ^ 3 ^ 2` evaluates to 64 instead of 512 — right-associativity of `^`
   is not implemented (it groups left instead of right).
3. Unary minus `-3 + 4` evaluates incorrectly.

## Files

- `src/pratt_parser.hpp` — tokenizer and Pratt parser
- `src/main.cpp` — test driver
