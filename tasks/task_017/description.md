# Bug Report: Application hangs when certain event combinations are triggered

## Summary

Our event-driven system uses an `EventBus` for decoupled communication between components. The `Dispatcher` routes domain events through the bus to registered handlers.

## Problem

The application intermittently hangs (becomes completely unresponsive) when processing certain sequences of events. It seems to happen when multiple handlers are registered and specific combinations of events are published. Eventually it crashes with a `RecursionError`.

Users report that it works fine when there are only a few handlers, but as more features were added with more event handlers, the system started hanging.

## Steps to Reproduce

1. Register multiple handlers that react to different event types
2. Trigger events that cause handlers to publish additional events
3. Under certain combinations, the system hangs or crashes

## Expected Behavior

The event system should handle any combination of event subscriptions gracefully. If a problematic event chain is detected, it should raise a clear error instead of hanging.

## Environment

- Python 3.10+
- Custom event bus system (no external dependencies)
