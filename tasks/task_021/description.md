# Task 021: Add Middleware Pipeline to Request Handler

## Current State

We have a simple request-handling setup spread across multiple files:

- `src/request.py` — `Request` and `Response` dataclasses
- `src/handler.py` — `RequestHandler` with a `handle(request)` method
- `src/app.py` — `App` class that wires everything together

The `App` class creates a `RequestHandler` and processes incoming requests. It works fine for simple cases but there's no way to hook into the request lifecycle — no logging, no auth checks, no request transformation.

## Feature Request

We need a middleware system. Something like Express.js or Django middleware where you can stack up processing layers. Each middleware should be able to:

- Inspect or modify the request before it reaches the handler
- Inspect or modify the response after the handler runs
- Short-circuit the chain entirely (e.g., return a 401 without ever hitting the handler)

A middleware is a callable that takes `(request, next_handler)` where `next_handler` is a callable that continues the chain. The middleware calls `next_handler(request)` to proceed, or returns its own Response to short-circuit.

The `App` class needs a `use(middleware)` method to register middleware. Middlewares execute in registration order, wrapping the core handler.

## Constraints

- Don't break existing request handling — basic requests without middleware must still work exactly as before.
- The middleware chain must compose correctly: first registered = outermost wrapper.
- Middleware must be able to both modify the request going in AND the response coming out.

## Acceptance Criteria

- [ ] `app.use(middleware_fn)` registers a middleware
- [ ] Middlewares execute in order of registration
- [ ] A middleware can modify request before passing it down
- [ ] A middleware can modify response coming back up
- [ ] A middleware can short-circuit by returning a Response without calling next
- [ ] Existing tests continue to pass
