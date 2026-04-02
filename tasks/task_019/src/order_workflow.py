"""Order workflow built on top of the state machine."""

from .state_machine import StateMachine, InvalidTransitionError


class OrderWorkflow:
    """Manages the lifecycle of an order using a state machine.

    States: draft, submitted, approved, rejected, fulfilled, cancelled
    Transitions:
        submit:   draft -> submitted
        approve:  submitted -> approved
        reject:   submitted -> rejected
        fulfill:  approved -> fulfilled
        cancel:   draft -> cancelled  (can also cancel from submitted)
        resubmit: rejected -> submitted
    """

    STATES = ["draft", "submitted", "approved", "rejected", "fulfilled", "cancelled"]

    def __init__(self, order_id: str, approver_required=True):
        self.order_id = order_id
        self.approver_required = approver_required
        self._notes = []
        self._sm = self._build_state_machine()

    def _build_state_machine(self) -> StateMachine:
        sm = StateMachine("draft")

        # Register all states
        for state in self.STATES:
            sm.add_state(state)

        # Register transitions
        sm.add_transition("submit", "draft", "submitted")
        sm.add_transition("approve", "submitted", "approved",
                         guard=self._can_approve)
        sm.add_transition("reject", "submitted", "rejected")
        sm.add_transition("fulfill", "approved", "fulfilled")
        sm.add_transition("cancel_draft", "draft", "cancelled")
        sm.add_transition("cancel_submitted", "submitted", "cancelled")
        sm.add_transition("resubmit", "rejected", "submitted")

        return sm

    def _can_approve(self, **context):
        """Guard: check if approval conditions are met."""
        if not self.approver_required:
            return True
        approver = context.get("approver")
        return approver is not None and approver != ""

    @property
    def state(self) -> str:
        return self._sm.state

    @property
    def history(self) -> list:
        return self._sm.history

    def submit(self):
        """Submit the order for review."""
        self._sm.trigger("submit")
        self._notes.append(f"Order {self.order_id} submitted for review")
        return self.state

    def approve(self, approver: str = None):
        """Approve the order."""
        self._sm.trigger("approve", approver=approver)
        self._notes.append(f"Order {self.order_id} approved by {approver}")
        return self.state

    def reject(self, reason: str = ""):
        """Reject the order."""
        self._sm.trigger("reject")
        self._notes.append(f"Order {self.order_id} rejected: {reason}")
        return self.state

    def fulfill(self):
        """Mark the order as fulfilled."""
        self._sm.trigger("fulfill")
        self._notes.append(f"Order {self.order_id} fulfilled")
        return self.state

    def cancel(self):
        """Cancel the order (from draft or submitted)."""
        if self._sm.state == "draft":
            self._sm.trigger("cancel_draft")
        elif self._sm.state == "submitted":
            self._sm.trigger("cancel_submitted")
        else:
            raise InvalidTransitionError(
                f"Cannot cancel from state {self._sm.state!r}"
            )
        self._notes.append(f"Order {self.order_id} cancelled")
        return self.state

    def resubmit(self):
        """Resubmit a rejected order."""
        self._sm.trigger("resubmit")
        self._notes.append(f"Order {self.order_id} resubmitted")
        return self.state

    def get_notes(self) -> list:
        return list(self._notes)

    def get_available_actions(self) -> list:
        return self._sm.get_available_transitions()
