"""Request router that dispatches to handlers based on path."""

import re

from .middleware import MiddlewareStack, Response


class Route:
    """Represents a single route."""

    def __init__(self, method, path_pattern, handler, name=None):
        self.method = method.upper()
        self.name = name or handler.__name__
        self._path_pattern = path_pattern
        self._handler = handler
        self._regex = self._compile_pattern(path_pattern)

    def _compile_pattern(self, pattern):
        """Convert a path pattern with {params} to a regex."""
        regex_pattern = re.sub(
            r'\{(\w+)\}',
            r'(?P<\1>[^/]+)',
            pattern
        )
        return re.compile(f'^{regex_pattern}$')

    def match(self, method, path):
        """Check if this route matches the given method and path."""
        if self.method != method.upper() and self.method != 'ANY':
            return None
        m = self._regex.match(path)
        if m:
            return m.groupdict()
        return None

    def handle(self, request, params=None):
        """Handle a request."""
        return self._handler(request, **(params or {}))


class Router:
    """HTTP router with middleware support.

    Routes requests to handlers and processes them through the
    middleware stack.
    """

    def __init__(self, middleware_stack=None):
        self._stack = middleware_stack or MiddlewareStack()
        self._routes = []
        self._not_found_handler = None
        self._before_dispatch = []
        self._after_dispatch = []

    @property
    def middleware_stack(self):
        return self._stack

    def add_route(self, method, path, handler, name=None):
        """Register a route."""
        self._routes.append(Route(method, path, handler, name))

    def get(self, path, handler, name=None):
        """Register a GET route."""
        self.add_route('GET', path, handler, name)

    def post(self, path, handler, name=None):
        """Register a POST route."""
        self.add_route('POST', path, handler, name)

    def set_not_found_handler(self, handler):
        """Set custom 404 handler."""
        self._not_found_handler = handler

    def _find_route(self, method, path):
        """Find matching route and extract params."""
        for route in self._routes:
            params = route.match(method, path)
            if params is not None:
                return route, params
        return None, None

    def dispatch(self, request):
        """Dispatch a request through middleware and to the appropriate handler."""
        route, params = self._find_route(request.method, request.path)

        if route is None:
            if self._not_found_handler:
                handler = lambda req: self._not_found_handler(req)
            else:
                handler = lambda req: Response(
                    status=404,
                    body={'error': f'No route found for {req.method} {req.path}'}
                )
        else:
            def handler(req):
                return route.handle(req, params)

        return self._stack.process_request(request, handler)

    def list_routes(self):
        """List all registered routes."""
        return [
            {'method': r.method, 'pattern': r._path_pattern, 'name': r.name}
            for r in self._routes
        ]
