import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.state_machine import StateMachine, InvalidTransitionError
from src.order_workflow import OrderWorkflow
from src.workflow_validator import validate_workflow, get_reachable_states


# ── pass-to-pass: basic state machine functionality ──────────────


class TestStateMachineBasic:
    def test_initial_state(self):
        sm = StateMachine("start")
        assert sm.state == "start"

    def test_simple_transition(self):
        sm = StateMachine("a")
        sm.add_state("b")
        sm.add_transition("go", "a", "b")
        sm.trigger("go")
        assert sm.state == "b"

    def test_history_tracking(self):
        sm = StateMachine("a")
        sm.add_state("b")
        sm.add_state("c")
        sm.add_transition("ab", "a", "b")
        sm.add_transition("bc", "b", "c")
        sm.trigger("ab")
        sm.trigger("bc")
        assert sm.history == ["a", "b", "c"]

    def test_unknown_transition_raises(self):
        sm = StateMachine("a")
        with pytest.raises(InvalidTransitionError, match="Unknown"):
            sm.trigger("nonexistent")

    def test_guard_blocks_transition(self):
        sm = StateMachine("a")
        sm.add_state("b")
        sm.add_transition("go", "a", "b", guard=lambda: False)
        with pytest.raises(InvalidTransitionError, match="[Gg]uard"):
            sm.trigger("go")

    def test_guard_allows_transition(self):
        sm = StateMachine("a")
        sm.add_state("b")
        sm.add_transition("go", "a", "b", guard=lambda: True)
        sm.trigger("go")
        assert sm.state == "b"

    def test_add_transition_duplicate_name_raises(self):
        sm = StateMachine("a")
        sm.add_state("b")
        sm.add_transition("go", "a", "b")
        with pytest.raises(ValueError, match="already exists"):
            sm.add_transition("go", "a", "b")

    def test_add_transition_invalid_source_raises(self):
        sm = StateMachine("a")
        sm.add_state("b")
        with pytest.raises(ValueError, match="not registered"):
            sm.add_transition("go", "unknown", "b")

    def test_get_available_transitions(self):
        sm = StateMachine("a")
        sm.add_state("b")
        sm.add_state("c")
        sm.add_transition("ab", "a", "b")
        sm.add_transition("bc", "b", "c")
        assert sm.get_available_transitions() == ["ab"]

    def test_can_trigger(self):
        sm = StateMachine("a")
        sm.add_state("b")
        sm.add_transition("go", "a", "b")
        assert sm.can_trigger("go") is True
        assert sm.can_trigger("unknown") is False

    def test_on_enter_callback(self):
        sm = StateMachine("a")
        sm.add_state("b")
        sm.add_transition("go", "a", "b")
        entered = []
        sm.on_enter("b", lambda: entered.append("b"))
        sm.trigger("go")
        assert entered == ["b"]

    def test_on_exit_callback(self):
        sm = StateMachine("a")
        sm.add_state("b")
        sm.add_transition("go", "a", "b")
        exited = []
        sm.on_exit("a", lambda: exited.append("a"))
        sm.trigger("go")
        assert exited == ["a"]


class TestOrderWorkflowHappyPath:
    def test_full_lifecycle(self):
        order = OrderWorkflow("ORD-001")
        assert order.state == "draft"
        order.submit()
        assert order.state == "submitted"
        order.approve(approver="manager")
        assert order.state == "approved"
        order.fulfill()
        assert order.state == "fulfilled"

    def test_reject_and_resubmit(self):
        order = OrderWorkflow("ORD-002")
        order.submit()
        order.reject(reason="missing info")
        assert order.state == "rejected"
        order.resubmit()
        assert order.state == "submitted"

    def test_cancel_from_draft(self):
        order = OrderWorkflow("ORD-003")
        order.cancel()
        assert order.state == "cancelled"

    def test_cancel_from_submitted(self):
        order = OrderWorkflow("ORD-004")
        order.submit()
        order.cancel()
        assert order.state == "cancelled"

    def test_notes_recorded(self):
        order = OrderWorkflow("ORD-005")
        order.submit()
        notes = order.get_notes()
        assert any("submitted" in n for n in notes)

    def test_no_approver_fails_guard(self):
        order = OrderWorkflow("ORD-006", approver_required=True)
        order.submit()
        with pytest.raises(InvalidTransitionError, match="[Gg]uard"):
            order.approve()  # no approver given

    def test_available_actions_from_draft(self):
        order = OrderWorkflow("ORD-007")
        actions = order.get_available_actions()
        assert "submit" in actions
        assert "cancel_draft" in actions
        assert "approve" not in actions


class TestWorkflowValidator:
    def test_reachable_from_draft(self):
        order = OrderWorkflow("ORD-V1")
        reachable = get_reachable_states(order._sm, "draft")
        assert "submitted" in reachable
        assert "approved" in reachable
        assert "fulfilled" in reachable
        assert "cancelled" in reachable


# ── fail-to-pass: invalid transitions should be blocked ──────────


class TestInvalidTransitions:
    @pytest.mark.fail_to_pass
    def test_approve_from_draft_rejected(self):
        """Cannot approve directly from draft — must submit first."""
        order = OrderWorkflow("ORD-BAD-1")
        assert order.state == "draft"
        with pytest.raises(InvalidTransitionError):
            order.approve(approver="manager")

    @pytest.mark.fail_to_pass
    def test_fulfill_from_draft_rejected(self):
        """Cannot fulfill from draft — must go through submit+approve."""
        order = OrderWorkflow("ORD-BAD-2")
        assert order.state == "draft"
        with pytest.raises(InvalidTransitionError):
            order.fulfill()

    @pytest.mark.fail_to_pass
    def test_reject_from_draft_rejected(self):
        """Cannot reject from draft — can only reject from submitted."""
        order = OrderWorkflow("ORD-BAD-3")
        assert order.state == "draft"
        with pytest.raises(InvalidTransitionError):
            order.reject(reason="nope")

    @pytest.mark.fail_to_pass
    def test_resubmit_from_draft_rejected(self):
        """Cannot resubmit from draft — only from rejected."""
        order = OrderWorkflow("ORD-BAD-4")
        assert order.state == "draft"
        with pytest.raises(InvalidTransitionError):
            order.resubmit()

    @pytest.mark.fail_to_pass
    def test_sm_trigger_wrong_source_state(self):
        """The state machine's trigger() must check current state matches
        the transition's source state."""
        sm = StateMachine("x")
        sm.add_state("y")
        sm.add_state("z")
        sm.add_transition("to_z", "y", "z")  # only valid from y
        # Currently in "x", should not be able to trigger "to_z"
        with pytest.raises(InvalidTransitionError):
            sm.trigger("to_z")

    @pytest.mark.fail_to_pass
    def test_fulfill_from_submitted_rejected(self):
        """Cannot fulfill directly from submitted — must approve first."""
        order = OrderWorkflow("ORD-BAD-5")
        order.submit()
        assert order.state == "submitted"
        with pytest.raises(InvalidTransitionError):
            order.fulfill()
