import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.request import Request, Response
from src.handler import RequestHandler
from src.app import App


# ── helpers ──────────────────────────────────────────────────────────

def make_request(method="GET", path="/", headers=None, body=None):
    return Request(method=method, path=path, headers=headers or {}, body=body)


def echo_handler(request):
    return {"echo": request.body, "path": request.path}


def greet_handler(request):
    name = request.body.get("name", "world") if isinstance(request.body, dict) else "world"
    return Response(status_code=200, body={"greeting": f"Hello, {name}!"})


# ── pass-to-pass: basic request handling ─────────────────────────────

class TestBasicRequestHandling:
    def test_simple_get(self):
        app = App()
        app.route("GET", "/hello", greet_handler)
        resp = app.process(make_request("GET", "/hello", body={"name": "Alice"}))
        assert resp.status_code == 200
        assert resp.body["greeting"] == "Hello, Alice!"

    def test_route_not_found(self):
        app = App()
        resp = app.process(make_request("GET", "/missing"))
        assert resp.status_code == 404

    def test_echo_post(self):
        app = App()
        app.route("POST", "/echo", echo_handler)
        resp = app.process(make_request("POST", "/echo", body={"data": 42}))
        assert resp.status_code == 200
        assert resp.body["echo"]["data"] == 42

    def test_multiple_routes(self):
        app = App()
        app.route("GET", "/a", lambda r: {"route": "a"})
        app.route("GET", "/b", lambda r: {"route": "b"})
        assert app.process(make_request("GET", "/a")).body["route"] == "a"
        assert app.process(make_request("GET", "/b")).body["route"] == "b"

    def test_method_matters(self):
        app = App()
        app.route("POST", "/data", echo_handler)
        resp = app.process(make_request("GET", "/data"))
        assert resp.status_code == 404


class TestRequestHandler:
    def test_handler_returns_response_directly(self):
        handler = RequestHandler()
        handler.register("GET", "/custom", lambda r: Response(201, body="created"))
        resp = handler.handle(make_request("GET", "/custom"))
        assert resp.status_code == 201
        assert resp.body == "created"

    def test_handler_exception_returns_500(self):
        def bad_handler(r):
            raise ValueError("boom")
        handler = RequestHandler()
        handler.register("GET", "/fail", bad_handler)
        resp = handler.handle(make_request("GET", "/fail"))
        assert resp.status_code == 500


class TestRequestResponse:
    def test_request_header_lookup(self):
        req = make_request(headers={"Content-Type": "application/json"})
        assert req.header("content-type") == "application/json"
        assert req.header("X-Missing", "nope") == "nope"

    def test_response_ok_property(self):
        assert Response(200).ok is True
        assert Response(201).ok is True
        assert Response(400).ok is False
        assert Response(500).ok is False

    def test_response_set_header(self):
        resp = Response(200)
        resp.set_header("X-Custom", "value")
        assert resp.headers["X-Custom"] == "value"


# ── fail-to-pass: middleware pipeline ────────────────────────────────

class TestMiddlewareRegistration:
    @pytest.mark.fail_to_pass
    def test_app_has_use_method(self):
        app = App()
        assert hasattr(app, "use") and callable(app.use)

    @pytest.mark.fail_to_pass
    def test_middleware_receives_request_and_next(self):
        """Middleware signature is (request, next_handler) -> Response."""
        received = {}

        def spy_middleware(request, next_handler):
            received["request"] = request
            received["next"] = next_handler
            return next_handler(request)

        app = App()
        app.use(spy_middleware)
        app.route("GET", "/test", lambda r: {"ok": True})
        app.process(make_request("GET", "/test"))

        assert "request" in received
        assert callable(received["next"])


class TestMiddlewareExecution:
    @pytest.mark.fail_to_pass
    def test_middleware_can_modify_request(self):
        """Middleware adds a header before the handler sees the request."""
        def add_header_mw(request, next_handler):
            request.headers["X-Added"] = "by-middleware"
            return next_handler(request)

        captured = {}
        def capture_handler(request):
            captured["header"] = request.header("X-Added")
            return {"ok": True}

        app = App()
        app.use(add_header_mw)
        app.route("GET", "/cap", capture_handler)
        app.process(make_request("GET", "/cap"))

        assert captured["header"] == "by-middleware"

    @pytest.mark.fail_to_pass
    def test_middleware_can_modify_response(self):
        """Middleware adds a header to the response on its way out."""
        def tag_response_mw(request, next_handler):
            response = next_handler(request)
            response.set_header("X-Tagged", "yes")
            return response

        app = App()
        app.use(tag_response_mw)
        app.route("GET", "/tag", lambda r: Response(200, body="hi"))
        resp = app.process(make_request("GET", "/tag"))

        assert resp.headers.get("X-Tagged") == "yes"
        assert resp.body == "hi"

    @pytest.mark.fail_to_pass
    def test_middleware_short_circuit(self):
        """Auth middleware returns 401 without calling next."""
        def auth_middleware(request, next_handler):
            if request.header("Authorization") == "":
                return Response(status_code=401, body={"error": "Unauthorized"})
            return next_handler(request)

        handler_called = {"called": False}
        def secret_handler(r):
            handler_called["called"] = True
            return {"secret": "data"}

        app = App()
        app.use(auth_middleware)
        app.route("GET", "/secret", secret_handler)

        # No auth header → 401, handler never called
        resp = app.process(make_request("GET", "/secret"))
        assert resp.status_code == 401
        assert handler_called["called"] is False

        # With auth header → 200
        resp2 = app.process(make_request("GET", "/secret",
                                          headers={"Authorization": "Bearer token123"}))
        assert resp2.status_code == 200


class TestMiddlewareOrdering:
    @pytest.mark.fail_to_pass
    def test_middlewares_execute_in_registration_order(self):
        """First registered = outermost, sees request first and response last."""
        order = []

        def mw_a(request, next_handler):
            order.append("A-before")
            response = next_handler(request)
            order.append("A-after")
            return response

        def mw_b(request, next_handler):
            order.append("B-before")
            response = next_handler(request)
            order.append("B-after")
            return response

        def mw_c(request, next_handler):
            order.append("C-before")
            response = next_handler(request)
            order.append("C-after")
            return response

        app = App()
        app.use(mw_a)
        app.use(mw_b)
        app.use(mw_c)
        app.route("GET", "/order", lambda r: Response(200))
        app.process(make_request("GET", "/order"))

        assert order == ["A-before", "B-before", "C-before",
                         "C-after", "B-after", "A-after"]

    @pytest.mark.fail_to_pass
    def test_short_circuit_stops_chain(self):
        """When middleware B short-circuits, C never runs."""
        order = []

        def mw_a(request, next_handler):
            order.append("A-before")
            response = next_handler(request)
            order.append("A-after")
            return response

        def mw_b(request, next_handler):
            order.append("B-short-circuit")
            return Response(403, body="Forbidden")

        def mw_c(request, next_handler):
            order.append("C-before")
            response = next_handler(request)
            order.append("C-after")
            return response

        app = App()
        app.use(mw_a)
        app.use(mw_b)
        app.use(mw_c)
        app.route("GET", "/blocked", lambda r: Response(200))
        resp = app.process(make_request("GET", "/blocked"))

        assert resp.status_code == 403
        assert "C-before" not in order
        assert order == ["A-before", "B-short-circuit", "A-after"]


class TestMiddlewareWithNoRoutes:
    @pytest.mark.fail_to_pass
    def test_middleware_runs_even_for_404(self):
        """Middleware wraps the handler, so it runs even if no route matches."""
        logged = []

        def logging_mw(request, next_handler):
            logged.append(f"{request.method} {request.path}")
            response = next_handler(request)
            logged.append(f"status={response.status_code}")
            return response

        app = App()
        app.use(logging_mw)
        resp = app.process(make_request("GET", "/nowhere"))
        assert resp.status_code == 404
        assert logged == ["GET /nowhere", "status=404"]
