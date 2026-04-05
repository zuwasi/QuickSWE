# NFA-to-DFA – Incorrect Epsilon Closure

## Problem

A mini regex engine builds an NFA from a simple regex pattern (supporting
concatenation, `|`, `*`, `+`, `?`) and converts it to a DFA via subset
construction. The epsilon-closure computation has bugs.

Users report:

1. The pattern `a|b` matches "a" but not "b" — the epsilon closure from the
   start state does not reach the branch for "b".
2. The pattern `a*` matches "" and "a" but not "aaa" — the closure after
   consuming one "a" does not loop back correctly.
3. Patterns with `+` (one or more) incorrectly accept the empty string.

## Files

- `src/regex_engine.hpp` — NFA construction and subset construction
- `src/main.cpp` — test driver
