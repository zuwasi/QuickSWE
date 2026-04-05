# Task 028: Middleware Pipeline Error Handler Order Bug

## Problem

A middleware pipeline executes error handlers in the wrong order. When multiple
error handlers are registered, the pipeline prepends each new handler to the
list instead of appending it, so the last-added handler runs first instead of
last. This breaks the expected layered error handling where outer middleware
should catch errors from inner middleware.

## Expected Behavior

Error handlers should execute in the order they were added (FIFO), just like
normal middleware. The first-added error handler should run first, giving each
layer a chance to handle or transform the error before passing to the next.

## Files

- `src/middleware.py` — Middleware pipeline with use() and handle_error()
