"""Task scheduler that uses dependency graph for execution ordering."""

import time
from .dependency_graph import DependencyGraph


class Task:
    """Represents a schedulable task."""

    def __init__(self, task_id: str, action=None):
        self.task_id = task_id
        self.action = action or (lambda: None)
        self.executed = False
        self.execution_time = None

    def execute(self):
        """Run the task's action."""
        self.execution_time = time.time()
        self.action()
        self.executed = True

    def __repr__(self):
        return f"Task({self.task_id!r})"


class TaskScheduler:
    """Schedules and executes tasks respecting dependency order."""

    def __init__(self):
        self._graph = DependencyGraph()
        self._tasks = {}
        self._execution_log = []

    def add_task(self, task_id: str, action=None, depends_on=None):
        """Register a task with optional dependencies.

        Args:
            task_id: Unique task identifier.
            action: Callable to execute.
            depends_on: List of task IDs this task depends on.
        """
        task = Task(task_id, action)
        self._tasks[task_id] = task
        self._graph.add_node(task_id)
        for dep in (depends_on or []):
            self._graph.add_dependency(task_id, dep)

    def run(self) -> list:
        """Execute all tasks in dependency order.

        Returns:
            List of task IDs in the order they were executed.

        Raises:
            ValueError: If a circular dependency is detected.
        """
        order = self._graph.resolve_order()
        self._execution_log = []
        for task_id in order:
            if task_id in self._tasks:
                self._tasks[task_id].execute()
                self._execution_log.append(task_id)
        return list(self._execution_log)

    def get_execution_log(self) -> list:
        """Return the execution log from the last run."""
        return list(self._execution_log)

    def get_task(self, task_id: str):
        """Retrieve a task by ID."""
        return self._tasks.get(task_id)

    def validate(self) -> bool:
        """Check if the current graph is valid (no cycles).

        Returns:
            True if valid, raises ValueError if cycles detected.
        """
        if self._graph.has_cycle():
            raise ValueError("Circular dependency detected")
        return True
