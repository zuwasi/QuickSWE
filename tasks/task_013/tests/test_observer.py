import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.observer import EventEmitter, TypedEventEmitter


# ─── fail_to_pass ───────────────────────────────────────────────

@pytest.mark.fail_to_pass
def test_listener_removing_self_does_not_skip_next():
    """When listener A removes itself during emit, listener B must still fire."""
    emitter = EventEmitter()
    calls = []

    def listener_a(data):
        calls.append("A")
        emitter.off("event", listener_a)

    def listener_b(data):
        calls.append("B")

    emitter.on("event", listener_a)
    emitter.on("event", listener_b)
    emitter.emit("event", "x")

    assert calls == ["A", "B"], f"Expected ['A', 'B'], got {calls}"


@pytest.mark.fail_to_pass
def test_once_does_not_skip_subsequent_listeners():
    """A once() listener must not skip the listener registered after it."""
    emitter = EventEmitter()
    calls = []

    def first(data):
        calls.append("first")

    def second(data):
        calls.append("second")

    emitter.once("ping", first)
    emitter.on("ping", second)

    emitter.emit("ping", None)
    assert calls == ["first", "second"], f"Expected both, got {calls}"


@pytest.mark.fail_to_pass
def test_multiple_once_listeners_all_fire():
    """Multiple once() listeners on the same event must all fire."""
    emitter = EventEmitter()
    calls = []

    for i in range(4):
        emitter.once("go", lambda d, idx=i: calls.append(idx))

    emitter.emit("go", None)
    assert calls == [0, 1, 2, 3], f"Expected [0,1,2,3], got {calls}"


# ─── pass_to_pass ───────────────────────────────────────────────

def test_basic_emit():
    """Simple on + emit works."""
    emitter = EventEmitter()
    results = []
    emitter.on("data", lambda v: results.append(v))
    emitter.emit("data", 42)
    assert results == [42]


def test_off_removes_listener():
    """off() prevents the listener from being called."""
    emitter = EventEmitter()
    results = []

    def handler(v):
        results.append(v)

    emitter.on("ev", handler)
    emitter.off("ev", handler)
    emitter.emit("ev", 1)
    assert results == []


def test_typed_emitter_rejects_unknown():
    """TypedEventEmitter raises on unknown events."""
    emitter = TypedEventEmitter(["start", "stop"])
    with pytest.raises(ValueError):
        emitter.on("unknown", lambda: None)
