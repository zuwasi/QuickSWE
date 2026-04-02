"""Scheduler — assigns tasks to time slots and resources using backtracking.

TODO: Implement the scheduling algorithm:
1. For each unassigned task, try possible start times and resource assignments.
2. Check all constraints after each tentative assignment.
3. Backtrack if any constraint is violated.
4. Return a Solution with the best (lowest makespan) valid schedule found,
   or None if no valid schedule exists.
"""

from .solution import Solution


class Scheduler:
    """Constraint-based scheduler using backtracking.

    Args:
        tasks: List of Task objects.
        resources: List of Resource objects.
        constraints: List of Constraint objects.
    """

    def __init__(self, tasks, resources, constraints=None):
        self._tasks = list(tasks)
        self._resources = list(resources)
        self._constraints = list(constraints) if constraints else []

    @property
    def tasks(self):
        return list(self._tasks)

    @property
    def resources(self):
        return list(self._resources)

    @property
    def constraints(self):
        return list(self._constraints)

    def solve(self, max_time=100):
        """Find a valid schedule.

        Args:
            max_time: Maximum time horizon to consider for scheduling.

        Returns:
            Solution object if a valid schedule is found, None otherwise.
        """
        # TODO: Implement backtracking scheduler
        raise NotImplementedError("Scheduler.solve() is not yet implemented")
