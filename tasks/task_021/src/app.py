"""Application class that wires together request handling."""

from src.request import Request, Response
from src.handler import RequestHandler


class App:
    """Main application entry point for processing requests."""

    def __init__(self):
        self._handler = RequestHandler()

    def route(self, method: str, path: str, handler_fn):
        """Register a route handler."""
        self._handler.register(method, path, handler_fn)

    def process(self, request: Request) -> Response:
        """Process an incoming request through the handler."""
        return self._handler.handle(request)
