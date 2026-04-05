# Task 029: Regex Engine Catastrophic Backtracking Bug

## Problem

A simple regex engine supporting `.`, `*`, `+`, and `?` quantifiers enters an
infinite loop when processing patterns with nested quantifiers like `(a+)+`
because it doesn't track positions where zero-length matches occur. The engine
keeps trying the same empty match over and over.

## Expected Behavior

The engine should detect when a quantified sub-expression matches zero characters
and stop iterating to prevent infinite loops. Patterns like `a+b` matching
"aaab" should complete in bounded time, and nested quantifiers should not cause
hangs.

## Files

- `src/regex_engine.py` — Simple regex matcher with backtracking
