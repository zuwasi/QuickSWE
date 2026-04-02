"""Constraint classes — define scheduling constraints.

TODO: Implement constraint checking logic.
Each constraint type has a `is_satisfied(assignments)` method that checks
whether the constraint is met given the current partial assignments.

assignments is a dict: { task_name: TaskAssignment } where TaskAssignment
has .start_time, .end_time, and .resources attributes.
"""


class Constraint:
    """Base class for scheduling constraints."""

    def is_satisfied(self, assignments):
        """Check if this constraint is satisfied given current assignments.

        Args:
            assignments: Dict mapping task_name -> TaskAssignment.

        Returns:
            True if satisfied (or if relevant tasks are not yet assigned).
        """
        raise NotImplementedError


class DependencyConstraint(Constraint):
    """Task A must complete before task B starts.

    Args:
        before_task: Name of the task that must come first.
        after_task: Name of the task that must come after.
    """

    def __init__(self, before_task, after_task):
        self._before = before_task
        self._after = after_task

    @property
    def before_task(self):
        return self._before

    @property
    def after_task(self):
        return self._after

    def is_satisfied(self, assignments):
        """Check that before_task ends before after_task starts.

        If either task is not yet assigned, the constraint is trivially satisfied.
        """
        # TODO: Implement
        raise NotImplementedError("DependencyConstraint.is_satisfied() not implemented")

    def __repr__(self):
        return f"DependencyConstraint({self._before!r} -> {self._after!r})"


class TimeWindowConstraint(Constraint):
    """Task must start after earliest_start and end before latest_end.

    Args:
        task_name: Name of the constrained task.
        earliest_start: Minimum start time.
        latest_end: Maximum end time.
    """

    def __init__(self, task_name, earliest_start, latest_end):
        self._task = task_name
        self._earliest = earliest_start
        self._latest = latest_end

    @property
    def task_name(self):
        return self._task

    @property
    def earliest_start(self):
        return self._earliest

    @property
    def latest_end(self):
        return self._latest

    def is_satisfied(self, assignments):
        """Check the task falls within the time window."""
        # TODO: Implement
        raise NotImplementedError("TimeWindowConstraint.is_satisfied() not implemented")

    def __repr__(self):
        return f"TimeWindowConstraint({self._task!r}, [{self._earliest}, {self._latest}])"


class ResourceConstraint(Constraint):
    """Task requires a resource of a specific type.

    Args:
        task_name: Name of the task.
        resource_type: The type of resource required.
    """

    def __init__(self, task_name, resource_type):
        self._task = task_name
        self._resource_type = resource_type

    @property
    def task_name(self):
        return self._task

    @property
    def resource_type(self):
        return self._resource_type

    def is_satisfied(self, assignments):
        """Check the task has been assigned a resource of the right type."""
        # TODO: Implement
        raise NotImplementedError("ResourceConstraint.is_satisfied() not implemented")

    def __repr__(self):
        return f"ResourceConstraint({self._task!r}, type={self._resource_type!r})"
