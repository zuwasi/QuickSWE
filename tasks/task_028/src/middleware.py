"""
Middleware pipeline framework supporting request/response processing
and layered error handling.
"""

from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import traceback


@dataclass
class Request:
    """Represents an incoming request."""
    method: str = "GET"
    path: str = "/"
    headers: Dict[str, str] = field(default_factory=dict)
    body: Any = None
    params: Dict[str, str] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Response:
    """Represents an outgoing response."""
    status: int = 200
    headers: Dict[str, str] = field(default_factory=dict)
    body: Any = None
    context: Dict[str, Any] = field(default_factory=dict)

    def set_error(self, status: int, message: str):
        self.status = status
        self.body = {"error": message}


class MiddlewareError(Exception):
    """Error raised within middleware processing."""
    def __init__(self, message: str, status: int = 500):
        super().__init__(message)
        self.status = status


MiddlewareFunc = Callable[[Request, Response, Callable], None]
ErrorHandlerFunc = Callable[[Exception, Request, Response, Callable], None]


class Pipeline:
    """Middleware pipeline that processes requests through a chain of handlers."""

    def __init__(self):
        self._middleware: List[Tuple[str, MiddlewareFunc]] = []
        self._error_handlers: List[Tuple[str, ErrorHandlerFunc]] = []
        self._before_hooks: List[Callable] = []
        self._after_hooks: List[Callable] = []
        self._execution_log: List[str] = []

    def use(self, middleware: MiddlewareFunc,
            name: Optional[str] = None) -> "Pipeline":
        mw_name = name or f"middleware_{len(self._middleware)}"
        self._middleware.append((mw_name, middleware))
        return self

    def handle_error(self, handler: ErrorHandlerFunc,
                     name: Optional[str] = None) -> "Pipeline":
        handler_name = name or f"error_handler_{len(self._error_handlers)}"
        self._error_handlers.insert(0, (handler_name, handler))
        return self

    def before(self, hook: Callable) -> "Pipeline":
        self._before_hooks.append(hook)
        return self

    def after(self, hook: Callable) -> "Pipeline":
        self._after_hooks.append(hook)
        return self

    def process(self, request: Request,
                response: Optional[Response] = None) -> Response:
        if response is None:
            response = Response()

        self._execution_log = []

        for hook in self._before_hooks:
            hook(request, response)

        try:
            self._run_middleware_chain(request, response, 0)
        except Exception as error:
            self._run_error_chain(error, request, response, 0)

        for hook in self._after_hooks:
            hook(request, response)

        return response

    def _run_middleware_chain(self, request: Request,
                              response: Response, index: int):
        if index >= len(self._middleware):
            return

        name, middleware = self._middleware[index]
        self._execution_log.append(f"middleware:{name}")

        def next_fn():
            self._run_middleware_chain(request, response, index + 1)

        middleware(request, response, next_fn)

    def _run_error_chain(self, error: Exception,
                          request: Request, response: Response,
                          index: int):
        if index >= len(self._error_handlers):
            if isinstance(error, MiddlewareError):
                response.set_error(error.status, str(error))
            else:
                response.set_error(500, str(error))
            return

        name, handler = self._error_handlers[index]
        self._execution_log.append(f"error_handler:{name}")

        def next_fn():
            self._run_error_chain(error, request, response, index + 1)

        try:
            handler(error, request, response, next_fn)
        except Exception as new_error:
            self._run_error_chain(new_error, request, response, index + 1)

    def get_execution_log(self) -> List[str]:
        return list(self._execution_log)

    def get_middleware_names(self) -> List[str]:
        return [name for name, _ in self._middleware]

    def get_error_handler_names(self) -> List[str]:
        return [name for name, _ in self._error_handlers]

    def remove_middleware(self, name: str) -> bool:
        for i, (n, _) in enumerate(self._middleware):
            if n == name:
                self._middleware.pop(i)
                return True
        return False

    def clear(self):
        self._middleware.clear()
        self._error_handlers.clear()
        self._before_hooks.clear()
        self._after_hooks.clear()


def create_logger_middleware(log_list: List[str]) -> MiddlewareFunc:
    def logger(req: Request, res: Response, next_fn: Callable):
        log_list.append(f">> {req.method} {req.path}")
        next_fn()
        log_list.append(f"<< {res.status}")
    return logger


def create_auth_middleware(valid_tokens: List[str]) -> MiddlewareFunc:
    def auth(req: Request, res: Response, next_fn: Callable):
        token = req.headers.get("Authorization", "")
        if token not in valid_tokens:
            raise MiddlewareError("Unauthorized", 401)
        req.context["authenticated"] = True
        next_fn()
    return auth


def create_cors_middleware(allowed_origins: List[str]) -> MiddlewareFunc:
    def cors(req: Request, res: Response, next_fn: Callable):
        origin = req.headers.get("Origin", "")
        if origin in allowed_origins or "*" in allowed_origins:
            res.headers["Access-Control-Allow-Origin"] = origin or "*"
        next_fn()
    return cors
