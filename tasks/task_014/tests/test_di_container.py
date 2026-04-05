import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.di_container import (
    Container, CircularDependencyError, ServiceNotFoundError, Lifetime,
)


# ─── fail_to_pass ───────────────────────────────────────────────

@pytest.mark.fail_to_pass
def test_direct_circular_dependency_raises():
    """A -> B -> A must raise CircularDependencyError, not RecursionError."""
    c = Container()
    c.register("A", lambda cont: cont.resolve("B"))
    c.register("B", lambda cont: cont.resolve("A"))

    with pytest.raises(CircularDependencyError):
        c.resolve("A")


@pytest.mark.fail_to_pass
def test_three_node_circular_dependency():
    """A -> B -> C -> A must raise CircularDependencyError."""
    c = Container()
    c.register("A", lambda cont: cont.resolve("B"))
    c.register("B", lambda cont: cont.resolve("C"))
    c.register("C", lambda cont: cont.resolve("A"))

    with pytest.raises(CircularDependencyError):
        c.resolve("A")


@pytest.mark.fail_to_pass
def test_circular_error_message_contains_cycle():
    """The error message must mention the services forming the cycle."""
    c = Container()
    c.register("X", lambda cont: cont.resolve("Y"))
    c.register("Y", lambda cont: cont.resolve("X"))

    with pytest.raises(CircularDependencyError, match=r"[XY].*[XY]"):
        c.resolve("X")


# ─── pass_to_pass ───────────────────────────────────────────────

def test_simple_resolution():
    """Non-circular resolution works."""
    c = Container()
    c.register("greeting", lambda cont: "hello")
    assert c.resolve("greeting") == "hello"


def test_singleton_returns_same_instance():
    """Singleton lifetime returns the same object."""
    c = Container()
    c.register("obj", lambda cont: object(), lifetime=Lifetime.SINGLETON)
    a = c.resolve("obj")
    b = c.resolve("obj")
    assert a is b


def test_service_not_found():
    """Resolving an unknown service raises ServiceNotFoundError."""
    c = Container()
    with pytest.raises(ServiceNotFoundError):
        c.resolve("nope")
