"""Solution — represents a valid schedule.

TODO: Implement Solution and TaskAssignment classes.
"""


class TaskAssignment:
    """Represents the scheduled assignment for a single task.

    Attributes:
        task_name: Name of the task.
        start_time: Start time (integer).
        end_time: End time (integer, = start_time + duration).
        resources: List of Resource objects assigned to this task.
    """

    def __init__(self, task_name, start_time, end_time, resources=None):
        self._task_name = task_name
        self._start_time = start_time
        self._end_time = end_time
        self._resources = list(resources) if resources else []

    @property
    def task_name(self):
        return self._task_name

    @property
    def start_time(self):
        return self._start_time

    @property
    def end_time(self):
        return self._end_time

    @property
    def resources(self):
        return list(self._resources)

    def __repr__(self):
        res_names = [r.name if hasattr(r, 'name') else str(r) for r in self._resources]
        return (f"TaskAssignment({self._task_name!r}, "
                f"start={self._start_time}, end={self._end_time}, "
                f"resources={res_names})")


class Solution:
    """Represents a complete valid schedule.

    Stores TaskAssignment objects for each scheduled task.
    """

    def __init__(self):
        self._assignments = {}  # task_name -> TaskAssignment

    def add_assignment(self, assignment):
        """Add a task assignment to the solution.

        Args:
            assignment: TaskAssignment object.
        """
        self._assignments[assignment.task_name] = assignment

    def get_assignment(self, task_name):
        """Get the assignment for a specific task.

        Args:
            task_name: Name of the task.

        Returns:
            TaskAssignment or None.
        """
        return self._assignments.get(task_name)

    @property
    def assignments(self):
        """Return dict of all assignments."""
        return dict(self._assignments)

    @property
    def makespan(self):
        """Return the makespan (latest end time across all tasks).

        Returns:
            int: The makespan, or 0 if no assignments.
        """
        if not self._assignments:
            return 0
        return max(a.end_time for a in self._assignments.values())

    def is_complete(self, task_names):
        """Check if all tasks have been assigned.

        Args:
            task_names: List of task names that should be scheduled.

        Returns:
            True if all tasks have assignments.
        """
        return all(name in self._assignments for name in task_names)

    def __repr__(self):
        return f"Solution(tasks={len(self._assignments)}, makespan={self.makespan})"
