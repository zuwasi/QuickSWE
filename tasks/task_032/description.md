# Task 032: Template Engine Nested Loop Variable Bug

## Problem

A template engine renders the wrong variable value in nested `{% for %}` blocks.
When an inner loop variable has a different name than the outer loop variable,
the inner loop's variable assignment overwrites the outer variable in the shared
context dictionary instead of creating a scoped shadow. After the inner loop
completes, the outer loop variable retains the last value from the inner loop.

## Expected Behavior

Each `{% for %}` block should shadow the context for its loop variable. When the
inner loop ends, the outer loop variable should be restored to its correct value
for the current iteration.

## Files

- `src/template_engine.py` — Template engine with variable interpolation and for loops
