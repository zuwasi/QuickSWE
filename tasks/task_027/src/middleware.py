"""Middleware stack for request processing."""


class Request:
    """Represents an HTTP request."""

    def __init__(self, path, method='GET', headers=None, body=None, subdomain=None):
        self.path = path
        self.method = method
        self.headers = headers or {}
        self.body = body
        self.subdomain = subdomain
        self._attributes = {}

    def set_attribute(self, key, value):
        """Set a request attribute."""
        self._attributes[key] = value

    def get_attribute(self, key, default=None):
        """Get a request attribute."""
        return self._attributes.get(key, default)

    def has_attribute(self, key):
        """Check if request has an attribute."""
        return key in self._attributes

    def __repr__(self):
        return f"Request({self.method} {self.path})"


class Response:
    """Represents an HTTP response."""

    def __init__(self, status=200, body=None, headers=None):
        self.status = status
        self.body = body
        self.headers = headers or {}

    def is_success(self):
        return 200 <= self.status < 300

    def is_error(self):
        return self.status >= 400

    def __repr__(self):
        return f"Response(status={self.status})"


class Middleware:
    """Base middleware class."""

    def __init__(self, name=None):
        self._name = name or self.__class__.__name__
        self._enabled = True

    @property
    def name(self):
        return self._name

    @property
    def enabled(self):
        return self._enabled

    def enable(self):
        self._enabled = True

    def disable(self):
        self._enabled = False

    def before_request(self, request):
        """Called before the request is handled. Return None to continue,
        or return a Response to short-circuit."""
        return None

    def after_request(self, request, response):
        """Called after the request is handled. Can modify the response."""
        return response


class MiddlewareStack:
    """Manages an ordered collection of middlewares.

    Middlewares are executed in the order they were added.
    before_request hooks run in order; after_request hooks run in reverse.
    """

    def __init__(self):
        self._middlewares = []
        self._error_handlers = []

    def add(self, middleware):
        """Add a middleware to the stack.

        BUG: Middlewares are simply appended in the order add() is called.
        There is no priority system, so the execution order depends entirely
        on the order of add() calls. If TenantMiddleware is added before
        AuthMiddleware, it will try to access request.user before auth sets it.
        """
        if not isinstance(middleware, Middleware):
            raise TypeError(f"Expected Middleware, got {type(middleware).__name__}")
        self._middlewares.append(middleware)

    def remove(self, name):
        """Remove a middleware by name."""
        self._middlewares = [m for m in self._middlewares if m.name != name]

    def add_error_handler(self, handler_fn):
        """Add an error handler."""
        self._error_handlers.append(handler_fn)

    def get_middleware(self, name):
        """Get a middleware by name."""
        for m in self._middlewares:
            if m.name == name:
                return m
        return None

    @property
    def middleware_names(self):
        """Return list of middleware names in order."""
        return [m.name for m in self._middlewares]

    def process_request(self, request, handler):
        """Process a request through the middleware stack.

        1. Run before_request hooks in order
        2. If none short-circuits, call the handler
        3. Run after_request hooks in reverse order
        """
        # Run before_request hooks
        for middleware in self._middlewares:
            if not middleware.enabled:
                continue
            try:
                result = middleware.before_request(request)
                if result is not None:
                    # Middleware short-circuited with a response
                    return result
            except Exception as e:
                return self._handle_error(e, request)

        # Call the actual handler
        try:
            response = handler(request)
        except Exception as e:
            return self._handle_error(e, request)

        # Run after_request hooks in reverse order
        for middleware in reversed(self._middlewares):
            if not middleware.enabled:
                continue
            try:
                response = middleware.after_request(request, response)
            except Exception as e:
                return self._handle_error(e, request)

        return response

    def _handle_error(self, error, request):
        """Handle errors during request processing."""
        for handler in self._error_handlers:
            try:
                result = handler(error, request)
                if result is not None:
                    return result
            except Exception:
                continue

        return Response(
            status=500,
            body={'error': str(error), 'type': type(error).__name__}
        )

    def __len__(self):
        return len(self._middlewares)

    def __repr__(self):
        names = ', '.join(m.name for m in self._middlewares)
        return f"MiddlewareStack([{names}])"
