"""Tests for the constraint-based scheduler."""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.task_model import Task
from src.resource import Resource
from src.constraint import DependencyConstraint, TimeWindowConstraint, ResourceConstraint
from src.scheduler import Scheduler
from src.solution import Solution, TaskAssignment


# ============================================================
# PASS-TO-PASS: Task and Resource model tests
# ============================================================

class TestTaskModel:
    def test_create_task(self):
        t = Task("build", 5, ["machine"])
        assert t.name == "build"
        assert t.duration == 5
        assert t.resource_types == ["machine"]

    def test_task_no_resources(self):
        t = Task("plan", 2)
        assert t.resource_types == []

    def test_task_invalid_duration(self):
        with pytest.raises(ValueError):
            Task("bad", 0)

    def test_task_equality(self):
        t1 = Task("x", 1)
        t2 = Task("x", 2)
        assert t1 == t2  # Same name => equal

    def test_task_hash(self):
        t1 = Task("x", 1)
        t2 = Task("x", 2)
        assert hash(t1) == hash(t2)


class TestResourceModel:
    def test_create_resource(self):
        r = Resource("Room A", "room", [(0, 10)])
        assert r.name == "Room A"
        assert r.resource_type == "room"

    def test_always_available(self):
        r = Resource("Bot", "worker")
        assert r.is_available(0, 100)
        assert r.is_available(500, 1000)

    def test_availability_window(self):
        r = Resource("Room", "room", [(8, 17)])
        assert r.is_available(9, 12) is True
        assert r.is_available(8, 17) is True
        assert r.is_available(16, 18) is False
        assert r.is_available(5, 9) is False

    def test_multiple_windows(self):
        r = Resource("Lab", "room", [(8, 12), (14, 18)])
        assert r.is_available(9, 11) is True
        assert r.is_available(14, 16) is True
        assert r.is_available(11, 15) is False


class TestSolutionModel:
    def test_empty_solution(self):
        sol = Solution()
        assert sol.makespan == 0

    def test_add_assignment(self):
        sol = Solution()
        sol.add_assignment(TaskAssignment("task1", 0, 5, []))
        assert sol.get_assignment("task1").start_time == 0
        assert sol.get_assignment("task1").end_time == 5

    def test_makespan(self):
        sol = Solution()
        sol.add_assignment(TaskAssignment("a", 0, 3, []))
        sol.add_assignment(TaskAssignment("b", 2, 7, []))
        assert sol.makespan == 7

    def test_is_complete(self):
        sol = Solution()
        sol.add_assignment(TaskAssignment("a", 0, 1, []))
        assert sol.is_complete(["a"]) is True
        assert sol.is_complete(["a", "b"]) is False


# ============================================================
# FAIL-TO-PASS: Scheduler and constraint tests
# ============================================================

@pytest.mark.fail_to_pass
class TestConstraintSatisfaction:
    """Test that individual constraints check correctly."""

    def test_dependency_satisfied(self):
        c = DependencyConstraint("A", "B")
        assignments = {
            "A": TaskAssignment("A", 0, 3, []),
            "B": TaskAssignment("B", 3, 6, []),
        }
        assert c.is_satisfied(assignments) is True

    def test_dependency_violated(self):
        c = DependencyConstraint("A", "B")
        assignments = {
            "A": TaskAssignment("A", 0, 5, []),
            "B": TaskAssignment("B", 3, 6, []),  # Starts before A ends
        }
        assert c.is_satisfied(assignments) is False

    def test_dependency_unassigned(self):
        """If one task isn't assigned yet, constraint is trivially satisfied."""
        c = DependencyConstraint("A", "B")
        assignments = {"A": TaskAssignment("A", 0, 3, [])}
        assert c.is_satisfied(assignments) is True

    def test_time_window_satisfied(self):
        c = TimeWindowConstraint("X", 5, 15)
        assignments = {"X": TaskAssignment("X", 5, 10, [])}
        assert c.is_satisfied(assignments) is True

    def test_time_window_violated_early(self):
        c = TimeWindowConstraint("X", 5, 15)
        assignments = {"X": TaskAssignment("X", 3, 8, [])}
        assert c.is_satisfied(assignments) is False

    def test_time_window_violated_late(self):
        c = TimeWindowConstraint("X", 5, 15)
        assignments = {"X": TaskAssignment("X", 10, 20, [])}
        assert c.is_satisfied(assignments) is False

    def test_resource_constraint_satisfied(self):
        r = Resource("Machine1", "machine")
        c = ResourceConstraint("build", "machine")
        assignments = {"build": TaskAssignment("build", 0, 5, [r])}
        assert c.is_satisfied(assignments) is True

    def test_resource_constraint_wrong_type(self):
        r = Resource("Room1", "room")
        c = ResourceConstraint("build", "machine")
        assignments = {"build": TaskAssignment("build", 0, 5, [r])}
        assert c.is_satisfied(assignments) is False


@pytest.mark.fail_to_pass
class TestSimpleScheduling:
    """Basic scheduler tests."""

    def test_single_task(self):
        tasks = [Task("A", 3)]
        resources = [Resource("R1", "any")]
        scheduler = Scheduler(tasks, resources)
        sol = scheduler.solve()
        assert sol is not None
        a = sol.get_assignment("A")
        assert a is not None
        assert a.end_time - a.start_time == 3

    def test_two_independent_tasks(self):
        tasks = [Task("A", 2), Task("B", 3)]
        resources = [Resource("R1", "any"), Resource("R2", "any")]
        scheduler = Scheduler(tasks, resources)
        sol = scheduler.solve()
        assert sol is not None
        assert sol.is_complete(["A", "B"])

    def test_two_tasks_with_dependency(self):
        tasks = [Task("A", 2), Task("B", 3)]
        resources = [Resource("R1", "any")]
        constraints = [DependencyConstraint("A", "B")]
        scheduler = Scheduler(tasks, resources, constraints)
        sol = scheduler.solve()
        assert sol is not None
        a = sol.get_assignment("A")
        b = sol.get_assignment("B")
        assert a.end_time <= b.start_time


@pytest.mark.fail_to_pass
class TestResourceScheduling:
    """Scheduler must handle resource conflicts."""

    def test_no_double_booking(self):
        """Two tasks that need the same room cannot overlap."""
        tasks = [Task("A", 3, ["room"]), Task("B", 3, ["room"])]
        resources = [Resource("Room1", "room")]
        constraints = [
            ResourceConstraint("A", "room"),
            ResourceConstraint("B", "room"),
        ]
        scheduler = Scheduler(tasks, resources, constraints)
        sol = scheduler.solve()
        assert sol is not None
        a = sol.get_assignment("A")
        b = sol.get_assignment("B")
        # No overlap
        assert a.end_time <= b.start_time or b.end_time <= a.start_time

    def test_two_rooms_parallel(self):
        """Two tasks needing rooms can run in parallel if two rooms available."""
        tasks = [Task("A", 3, ["room"]), Task("B", 3, ["room"])]
        resources = [Resource("Room1", "room"), Resource("Room2", "room")]
        constraints = [
            ResourceConstraint("A", "room"),
            ResourceConstraint("B", "room"),
        ]
        scheduler = Scheduler(tasks, resources, constraints)
        sol = scheduler.solve()
        assert sol is not None
        # They CAN overlap (makespan could be as low as 3)
        assert sol.makespan <= 6  # At worst sequential

    def test_resource_availability_respected(self):
        tasks = [Task("A", 2, ["lab"])]
        resources = [Resource("Lab1", "lab", [(5, 10)])]
        constraints = [ResourceConstraint("A", "lab")]
        scheduler = Scheduler(tasks, resources, constraints)
        sol = scheduler.solve()
        assert sol is not None
        a = sol.get_assignment("A")
        assert a.start_time >= 5
        assert a.end_time <= 10


@pytest.mark.fail_to_pass
class TestImpossibleSchedule:
    """Scheduler returns None for impossible schedules."""

    def test_no_valid_schedule(self):
        """Task needs 5 units but resource only available for 3."""
        tasks = [Task("A", 5, ["machine"])]
        resources = [Resource("M1", "machine", [(0, 3)])]
        constraints = [ResourceConstraint("A", "machine")]
        scheduler = Scheduler(tasks, resources, constraints)
        sol = scheduler.solve(max_time=20)
        assert sol is None

    def test_circular_dependency_impossible(self):
        """A before B, B before A — impossible."""
        tasks = [Task("A", 1), Task("B", 1)]
        resources = [Resource("R1", "any")]
        constraints = [
            DependencyConstraint("A", "B"),
            DependencyConstraint("B", "A"),
        ]
        scheduler = Scheduler(tasks, resources, constraints)
        sol = scheduler.solve(max_time=20)
        assert sol is None

    def test_time_window_too_small(self):
        """Task duration exceeds time window."""
        tasks = [Task("A", 5)]
        resources = [Resource("R1", "any")]
        constraints = [TimeWindowConstraint("A", 0, 3)]
        scheduler = Scheduler(tasks, resources, constraints)
        sol = scheduler.solve()
        assert sol is None


@pytest.mark.fail_to_pass
class TestComplexScheduling:
    """Multi-task scheduling with mixed constraints."""

    def test_chain_of_three(self):
        """A -> B -> C dependency chain."""
        tasks = [Task("A", 2), Task("B", 3), Task("C", 1)]
        resources = [Resource("R1", "any")]
        constraints = [
            DependencyConstraint("A", "B"),
            DependencyConstraint("B", "C"),
        ]
        scheduler = Scheduler(tasks, resources, constraints)
        sol = scheduler.solve()
        assert sol is not None
        a = sol.get_assignment("A")
        b = sol.get_assignment("B")
        c = sol.get_assignment("C")
        assert a.end_time <= b.start_time
        assert b.end_time <= c.start_time

    def test_five_tasks_with_constraints(self):
        """Complex 5-task schedule."""
        tasks = [
            Task("design", 2),
            Task("frontend", 3, ["dev"]),
            Task("backend", 4, ["dev"]),
            Task("testing", 2, ["dev"]),
            Task("deploy", 1),
        ]
        resources = [
            Resource("Dev1", "dev"),
            Resource("Dev2", "dev"),
        ]
        constraints = [
            DependencyConstraint("design", "frontend"),
            DependencyConstraint("design", "backend"),
            DependencyConstraint("frontend", "testing"),
            DependencyConstraint("backend", "testing"),
            DependencyConstraint("testing", "deploy"),
            ResourceConstraint("frontend", "dev"),
            ResourceConstraint("backend", "dev"),
            ResourceConstraint("testing", "dev"),
        ]
        scheduler = Scheduler(tasks, resources, constraints)
        sol = scheduler.solve()
        assert sol is not None
        assert sol.is_complete(["design", "frontend", "backend", "testing", "deploy"])

        # Verify all dependencies
        design = sol.get_assignment("design")
        frontend = sol.get_assignment("frontend")
        backend = sol.get_assignment("backend")
        testing = sol.get_assignment("testing")
        deploy = sol.get_assignment("deploy")

        assert design.end_time <= frontend.start_time
        assert design.end_time <= backend.start_time
        assert frontend.end_time <= testing.start_time
        assert backend.end_time <= testing.start_time
        assert testing.end_time <= deploy.start_time

    def test_time_window_with_dependency(self):
        """A must happen before B, and B must start in [5, 15]."""
        tasks = [Task("A", 2), Task("B", 3)]
        resources = [Resource("R1", "any")]
        constraints = [
            DependencyConstraint("A", "B"),
            TimeWindowConstraint("B", 5, 15),
        ]
        scheduler = Scheduler(tasks, resources, constraints)
        sol = scheduler.solve()
        assert sol is not None
        a = sol.get_assignment("A")
        b = sol.get_assignment("B")
        assert a.end_time <= b.start_time
        assert b.start_time >= 5
        assert b.end_time <= 15

    def test_makespan_reasonable(self):
        """Two independent tasks with two resources should run in parallel."""
        tasks = [Task("A", 5, ["machine"]), Task("B", 5, ["machine"])]
        resources = [Resource("M1", "machine"), Resource("M2", "machine")]
        constraints = [
            ResourceConstraint("A", "machine"),
            ResourceConstraint("B", "machine"),
        ]
        scheduler = Scheduler(tasks, resources, constraints)
        sol = scheduler.solve()
        assert sol is not None
        # With 2 machines, both can run in parallel => makespan should be 5
        assert sol.makespan <= 5
