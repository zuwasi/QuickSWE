import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.deadlock_detector import WaitForGraph, LockManager


class TestBasicDeadlock:
    """Tests that should pass both before and after the fix."""

    @pytest.mark.pass_to_pass
    def test_no_cycle_linear(self):
        g = WaitForGraph()
        g.add_edge("T1", "T2")
        g.add_edge("T2", "T3")
        assert g.detect_deadlock() is None

    @pytest.mark.pass_to_pass
    def test_real_cycle_detected(self):
        g = WaitForGraph()
        g.add_edge("T1", "T2")
        g.add_edge("T2", "T3")
        g.add_edge("T3", "T1")
        cycle = g.detect_deadlock()
        assert cycle is not None
        assert len(cycle) >= 3

    @pytest.mark.pass_to_pass
    def test_lock_acquire_release(self):
        lm = LockManager()
        success, cycle = lm.try_acquire("T1", "L1")
        assert success is True
        assert cycle is None
        lm.release("T1", "L1")


class TestSelfLoopFalsePositive:
    """Tests that should fail before the fix and pass after."""

    @pytest.mark.fail_to_pass
    def test_self_loop_not_deadlock(self):
        """A self-loop should NOT be reported as a deadlock."""
        g = WaitForGraph()
        g.add_node("T1")
        g.add_edge("T1", "T1")
        cycle = g.detect_deadlock()
        assert cycle is None, (
            f"Self-loop was incorrectly reported as deadlock: {cycle}"
        )

    @pytest.mark.fail_to_pass
    def test_self_loop_with_other_edges(self):
        """Self-loop mixed with non-cyclic edges should not be deadlock."""
        g = WaitForGraph()
        g.add_edge("T1", "T1")  # self-loop
        g.add_edge("T1", "T2")  # not a cycle
        g.add_edge("T2", "T3")  # not a cycle
        cycle = g.detect_deadlock()
        assert cycle is None, (
            f"False positive deadlock with self-loop: {cycle}"
        )

    @pytest.mark.fail_to_pass
    def test_reentrant_lock_no_false_deadlock(self):
        """Re-acquiring own non-reentrant lock should fail but not report deadlock."""
        lm = LockManager(enable_deadlock_detection=True)
        lm.register_lock("L1", reentrant=False)

        success, cycle = lm.try_acquire("T1", "L1")
        assert success is True

        # T1 tries to acquire L1 again (non-reentrant)
        success2, cycle2 = lm.try_acquire("T1", "L1")
        assert success2 is False, "Should fail to re-acquire non-reentrant lock"
        assert cycle2 is None, (
            f"Re-entrant acquire should not be reported as deadlock, got cycle: {cycle2}"
        )
