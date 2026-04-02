"""Core request handler with route-based dispatch."""

from src.request import Request, Response


class RequestHandler:
    """Handles incoming requests by dispatching to registered routes."""

    def __init__(self):
        self._routes = {}

    def register(self, method: str, path: str, handler_fn):
        """Register a handler function for a method + path combo."""
        key = (method.upper(), path)
        self._routes[key] = handler_fn

    def handle(self, request: Request) -> Response:
        """Process a request and return a response."""
        key = (request.method.upper(), request.path)
        handler_fn = self._routes.get(key)

        if handler_fn is None:
            return Response(status_code=404, body={"error": "Not Found"})

        try:
            result = handler_fn(request)
            if isinstance(result, Response):
                return result
            return Response(status_code=200, body=result)
        except Exception as e:
            return Response(status_code=500, body={"error": str(e)})
