# Task 027: AST Variable Renamer Scope Bug

## Problem

A Python AST transformer that renames variables incorrectly renames variables
inside nested function definitions that shadow the target variable. When a
nested function has its own local variable with the same name as the target,
the renamer should leave that inner scope alone, but instead it renames those
variables too, breaking scope correctness.

## Expected Behavior

Only variables in the target scope should be renamed. If a nested function
defines its own local with the same name, that inner function's references
should be left unchanged.

## Files

- `src/ast_rename.py` — AST-based variable renamer
