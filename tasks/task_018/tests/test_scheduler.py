import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.dependency_graph import DependencyGraph
from src.task_scheduler import TaskScheduler
from src.graph_utils import build_graph_from_dict, find_roots, find_leaves


# ── pass-to-pass: basic graph and scheduler operations ────────────


class TestDependencyGraphBasic:
    def test_add_node(self):
        g = DependencyGraph()
        g.add_node("A")
        assert "A" in g.get_all_nodes()

    def test_add_dependency(self):
        g = DependencyGraph()
        g.add_dependency("A", "B")
        assert "B" in g.get_dependencies("A")
        assert "A" in g.get_dependents("B")

    def test_simple_chain_order(self):
        g = DependencyGraph()
        g.add_dependency("C", "B")
        g.add_dependency("B", "A")
        order = g.resolve_order()
        assert order.index("A") < order.index("B")
        assert order.index("B") < order.index("C")

    def test_independent_nodes(self):
        g = DependencyGraph()
        g.add_node("X")
        g.add_node("Y")
        order = g.resolve_order()
        assert set(order) == {"X", "Y"}

    def test_single_node(self):
        g = DependencyGraph()
        g.add_node("solo")
        order = g.resolve_order()
        assert order == ["solo"]


class TestSchedulerBasic:
    def test_simple_chain(self):
        sched = TaskScheduler()
        log = []
        sched.add_task("A", action=lambda: log.append("A"))
        sched.add_task("B", action=lambda: log.append("B"), depends_on=["A"])
        sched.add_task("C", action=lambda: log.append("C"), depends_on=["B"])
        sched.run()
        assert log == ["A", "B", "C"]

    def test_tasks_marked_executed(self):
        sched = TaskScheduler()
        sched.add_task("X")
        sched.run()
        assert sched.get_task("X").executed is True

    def test_no_tasks(self):
        sched = TaskScheduler()
        result = sched.run()
        assert result == []


class TestGraphUtils:
    def test_build_from_dict(self):
        g = build_graph_from_dict({"A": ["B"], "B": [], "C": ["B"]})
        assert g.get_dependencies("A") == {"B"}
        assert g.get_dependencies("C") == {"B"}

    def test_find_roots(self):
        g = build_graph_from_dict({"A": ["B"], "B": [], "C": ["B"]})
        assert find_roots(g) == {"B"}

    def test_find_leaves(self):
        g = build_graph_from_dict({"A": ["B"], "B": [], "C": ["B"]})
        assert find_leaves(g) == {"A", "C"}


# ── pass-to-pass: diamond patterns resolve correctly ──────────────


class TestDiamondPattern:
    def test_diamond_no_duplicates(self):
        """Diamond dependency: A->B, A->C, B->D, C->D.
        D should appear exactly once in the ordering."""
        g = DependencyGraph()
        g.add_dependency("A", "B")
        g.add_dependency("A", "C")
        g.add_dependency("B", "D")
        g.add_dependency("C", "D")
        order = g.resolve_order()

        # No duplicates
        assert len(order) == len(set(order)), (
            f"Duplicates found in ordering: {order}"
        )
        # D before B and C, B and C before A
        assert order.index("D") < order.index("B")
        assert order.index("D") < order.index("C")
        assert order.index("B") < order.index("A")
        assert order.index("C") < order.index("A")

    def test_complex_diamond_no_duplicates(self):
        """Larger diamond: multiple shared dependencies."""
        g = DependencyGraph()
        # E depends on C, D
        # C depends on A, B
        # D depends on A, B
        g.add_dependency("E", "C")
        g.add_dependency("E", "D")
        g.add_dependency("C", "A")
        g.add_dependency("C", "B")
        g.add_dependency("D", "A")
        g.add_dependency("D", "B")
        order = g.resolve_order()

        assert len(order) == 5, f"Expected 5 unique nodes, got {len(order)}: {order}"
        assert len(order) == len(set(order)), f"Duplicates: {order}"

    def test_scheduler_diamond_runs_each_once(self):
        """Tasks in a diamond pattern should each execute exactly once."""
        sched = TaskScheduler()
        counts = {"D": 0, "B": 0, "C": 0, "A": 0}
        sched.add_task("D", action=lambda: counts.__setitem__("D", counts["D"] + 1))
        sched.add_task("B", action=lambda: counts.__setitem__("B", counts["B"] + 1),
                       depends_on=["D"])
        sched.add_task("C", action=lambda: counts.__setitem__("C", counts["C"] + 1),
                       depends_on=["D"])
        sched.add_task("A", action=lambda: counts.__setitem__("A", counts["A"] + 1),
                       depends_on=["B", "C"])
        result = sched.run()

        for task_id, count in counts.items():
            assert count == 1, f"Task {task_id} ran {count} times, expected 1"
        assert len(result) == 4, f"Expected 4 executions, got {len(result)}"


# ── fail-to-pass: cycle detection and false positives ─────────────


class TestCycleDetection:
    @pytest.mark.fail_to_pass
    def test_cycle_detected_in_resolve(self):
        """resolve_order should raise ValueError when a cycle exists."""
        g = DependencyGraph()
        g.add_dependency("A", "B")
        g.add_dependency("B", "C")
        g.add_dependency("C", "A")
        with pytest.raises(ValueError, match="[Cc]ycl"):
            g.resolve_order()

    @pytest.mark.fail_to_pass
    def test_self_cycle(self):
        """A node depending on itself should be detected as a cycle."""
        g = DependencyGraph()
        g.add_dependency("A", "A")
        with pytest.raises(ValueError, match="[Cc]ycl"):
            g.resolve_order()

    @pytest.mark.fail_to_pass
    def test_diamond_not_false_positive_cycle(self):
        """Diamond pattern is NOT a cycle — has_cycle() should return False."""
        g = DependencyGraph()
        g.add_dependency("A", "B")
        g.add_dependency("A", "C")
        g.add_dependency("B", "D")
        g.add_dependency("C", "D")
        assert g.has_cycle() is False, (
            "Diamond pattern falsely detected as cycle"
        )

    @pytest.mark.fail_to_pass
    def test_scheduler_validate_diamond(self):
        """Scheduler validation should accept diamond dependencies."""
        sched = TaskScheduler()
        sched.add_task("D")
        sched.add_task("B", depends_on=["D"])
        sched.add_task("C", depends_on=["D"])
        sched.add_task("A", depends_on=["B", "C"])
        # Should not raise — diamond is valid
        try:
            sched.validate()
        except ValueError as e:
            pytest.fail(f"Diamond pattern incorrectly rejected: {e}")

    @pytest.mark.fail_to_pass
    def test_scheduler_validate_real_cycle(self):
        """Scheduler should detect actual cycles during run()."""
        sched = TaskScheduler()
        sched.add_task("A", depends_on=["C"])
        sched.add_task("B", depends_on=["A"])
        sched.add_task("C", depends_on=["B"])
        with pytest.raises(ValueError, match="[Cc]ycl"):
            sched.run()
