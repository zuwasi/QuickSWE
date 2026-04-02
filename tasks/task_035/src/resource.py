"""Resource model — represents a resource with availability windows."""


class Resource:
    """A resource that can be assigned to tasks.

    Attributes:
        name: Unique resource name (e.g., "Room A", "Projector 1").
        resource_type: Type category (e.g., "room", "projector", "person").
        availability: List of (start, end) tuples representing available time windows.
                      The resource can only be used during these windows.
                      Each window is [start, end) — exclusive end.
    """

    def __init__(self, name, resource_type, availability=None):
        """Initialize a resource.

        Args:
            name: Unique resource name.
            resource_type: Type string (used to match task requirements).
            availability: List of (start, end) time windows. If None, always available.
        """
        self._name = name
        self._resource_type = resource_type
        self._availability = list(availability) if availability else None

    @property
    def name(self):
        return self._name

    @property
    def resource_type(self):
        return self._resource_type

    @property
    def availability(self):
        if self._availability is None:
            return None
        return list(self._availability)

    def is_available(self, start, end):
        """Check if the resource is available for the entire interval [start, end).

        Args:
            start: Start time (inclusive).
            end: End time (exclusive).

        Returns:
            True if the resource is available for the entire interval.
        """
        if self._availability is None:
            return True  # Always available
        for avail_start, avail_end in self._availability:
            if avail_start <= start and end <= avail_end:
                return True
        return False

    def __repr__(self):
        return f"Resource({self._name!r}, type={self._resource_type!r})"

    def __eq__(self, other):
        return isinstance(other, Resource) and self._name == other._name

    def __hash__(self):
        return hash(self._name)
