"""Task model — represents a schedulable task."""


class Task:
    """A task to be scheduled.

    Attributes:
        name: Unique task name.
        duration: Duration in time units (integer >= 1).
        resource_types: List of resource type strings this task requires.
                        The task needs one resource of each listed type.
    """

    def __init__(self, name, duration, resource_types=None):
        """Initialize a task.

        Args:
            name: Unique task name.
            duration: Duration in integer time units.
            resource_types: List of resource type strings needed (e.g., ['room', 'projector']).
        """
        if duration < 1:
            raise ValueError(f"Duration must be >= 1, got {duration}")
        self._name = name
        self._duration = duration
        self._resource_types = list(resource_types) if resource_types else []

    @property
    def name(self):
        return self._name

    @property
    def duration(self):
        return self._duration

    @property
    def resource_types(self):
        return list(self._resource_types)

    def __repr__(self):
        return f"Task({self._name!r}, duration={self._duration}, resources={self._resource_types})"

    def __eq__(self, other):
        return isinstance(other, Task) and self._name == other._name

    def __hash__(self):
        return hash(self._name)
