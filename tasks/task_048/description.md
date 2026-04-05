# Task 048: Incremental Parser Error Recovery State Loss

## Description

An incremental parser for a simple expression language supports parsing, error
recovery, and incremental updates. When a syntax error is encountered, the error
recovery mechanism should unwind the parse stack to find a recovery point (like a
statement boundary) and continue parsing from there.

## Bug

The error recovery resets the ENTIRE parse stack instead of just unwinding to the
nearest error recovery point. This means all successfully parsed nodes before the
error are lost, and the resulting AST contains only nodes parsed after the error.

## Expected Behavior

Error recovery should pop the stack only until it finds an appropriate recovery
point (e.g., a statement boundary), preserving all successfully parsed statements
before the error.
