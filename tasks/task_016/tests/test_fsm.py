import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.fsm import FiniteStateMachine, InvalidTransitionError


# ─── fail_to_pass ───────────────────────────────────────────────

@pytest.mark.fail_to_pass
def test_invalid_transition_raises_error():
    """Triggering an undefined event must raise InvalidTransitionError."""
    fsm = FiniteStateMachine("idle")
    fsm.add_transition("idle", "start", "running")

    with pytest.raises(InvalidTransitionError):
        fsm.trigger("stop")


@pytest.mark.fail_to_pass
def test_event_valid_in_other_state_raises():
    """An event valid for state B must not be accepted while in state A."""
    fsm = FiniteStateMachine("idle")
    fsm.add_transition("idle", "start", "running")
    fsm.add_transition("running", "stop", "idle")

    with pytest.raises(InvalidTransitionError):
        fsm.trigger("stop")

    assert fsm.state == "idle"


@pytest.mark.fail_to_pass
def test_state_unchanged_after_invalid_trigger():
    """After a rejected transition the state must not change."""
    fsm = FiniteStateMachine("locked")
    fsm.add_transition("locked", "unlock", "unlocked")
    fsm.add_transition("unlocked", "push", "open")

    try:
        fsm.trigger("push")
    except (InvalidTransitionError, Exception):
        pass

    assert fsm.state == "locked", f"State should remain 'locked', got '{fsm.state}'"


# ─── pass_to_pass ───────────────────────────────────────────────

def test_valid_transition():
    """A registered transition works correctly."""
    fsm = FiniteStateMachine("off")
    fsm.add_transition("off", "turn_on", "on")
    fsm.trigger("turn_on")
    assert fsm.state == "on"


def test_transition_callback():
    """Callbacks fire on valid transitions."""
    results = []
    fsm = FiniteStateMachine("a")
    fsm.add_transition("a", "go", "b", callback=lambda s, t, c: results.append((s, t)))
    fsm.trigger("go")
    assert results == [("a", "b")]


def test_history_tracking():
    """History records all state changes."""
    fsm = FiniteStateMachine("s1")
    fsm.add_transition("s1", "next", "s2")
    fsm.add_transition("s2", "next", "s3")
    fsm.trigger("next")
    fsm.trigger("next")
    assert fsm.history == ["s1", "s2", "s3"]


def test_available_events():
    """available_events returns only events for the current state."""
    fsm = FiniteStateMachine("idle")
    fsm.add_transition("idle", "start", "running")
    fsm.add_transition("idle", "configure", "config")
    fsm.add_transition("running", "stop", "idle")

    assert sorted(fsm.available_events()) == ["configure", "start"]
