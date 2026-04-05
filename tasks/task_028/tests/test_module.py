import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.middleware import Pipeline, Request, Response, MiddlewareError


class TestMiddlewarePassToPass:
    """Tests that should pass both before and after the fix."""

    def test_basic_middleware_chain(self):
        pipe = Pipeline()
        log = []
        pipe.use(lambda req, res, nxt: (log.append("a"), nxt()), name="a")
        pipe.use(lambda req, res, nxt: (log.append("b"), nxt()), name="b")
        pipe.process(Request())
        assert log == ["a", "b"]

    def test_middleware_modifies_response(self):
        pipe = Pipeline()
        def set_body(req, res, nxt):
            nxt()
            res.body = "hello"
        pipe.use(set_body)
        resp = pipe.process(Request())
        assert resp.body == "hello"

    def test_error_handler_catches_exception(self):
        pipe = Pipeline()
        def failing(req, res, nxt):
            raise ValueError("boom")
        def handler(err, req, res, nxt):
            res.set_error(500, str(err))
        pipe.use(failing)
        pipe.handle_error(handler, name="catch")
        resp = pipe.process(Request())
        assert resp.status == 500


@pytest.mark.fail_to_pass
class TestMiddlewareFailToPass:
    """Tests that fail before the fix and pass after."""

    def test_error_handlers_run_in_registration_order(self):
        pipe = Pipeline()
        order = []

        def handler_a(err, req, res, nxt):
            order.append("a")
            nxt()

        def handler_b(err, req, res, nxt):
            order.append("b")
            nxt()

        def handler_c(err, req, res, nxt):
            order.append("c")
            res.set_error(500, str(err))

        pipe.use(lambda req, res, nxt: (_ for _ in ()).throw(ValueError("fail")))
        pipe.handle_error(handler_a, name="a")
        pipe.handle_error(handler_b, name="b")
        pipe.handle_error(handler_c, name="c")
        pipe.process(Request())
        assert order == ["a", "b", "c"]

    def test_error_handler_names_in_order(self):
        pipe = Pipeline()
        pipe.handle_error(lambda e, req, res, nxt: nxt(), name="first")
        pipe.handle_error(lambda e, req, res, nxt: nxt(), name="second")
        pipe.handle_error(lambda e, req, res, nxt: nxt(), name="third")
        names = pipe.get_error_handler_names()
        assert names == ["first", "second", "third"]

    def test_first_handler_can_transform_error(self):
        pipe = Pipeline()
        transformed = []

        def failing(req, res, nxt):
            raise ValueError("original")

        def transform_handler(err, req, res, nxt):
            res.context["error_type"] = type(err).__name__
            res.set_error(400, "transformed")

        def fallback_handler(err, req, res, nxt):
            transformed.append("fallback_reached")
            res.set_error(500, str(err))

        pipe.use(failing)
        pipe.handle_error(transform_handler, name="transform")
        pipe.handle_error(fallback_handler, name="fallback")
        resp = pipe.process(Request())
        assert resp.status == 400
        assert resp.body == {"error": "transformed"}
        assert len(transformed) == 0
