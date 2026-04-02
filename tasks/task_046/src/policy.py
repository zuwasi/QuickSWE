"""Policy engine for access control decisions."""

from .principal import User
from .resource import Resource


class PolicyEngine:
    """Evaluates access control decisions using an AccessGraph.

    Uses the AccessGraph to resolve effective permissions and
    determine whether a user has access to a resource.
    """

    def __init__(self, access_graph):
        """Initialize with an AccessGraph.

        Args:
            access_graph: An AccessGraph instance for permission resolution.
        """
        self._graph = access_graph

    def check_access(self, user: User, resource: Resource,
                     permission: str) -> bool:
        """Check if a user has a specific permission on a resource.

        Args:
            user: The user requesting access.
            resource: The resource being accessed.
            permission: The permission type (read, write, delete, admin).

        Returns:
            True if access is allowed, False otherwise.
        """
        raise NotImplementedError("PolicyEngine.check_access not yet implemented")

    def get_all_permissions(self, user: User, resource: Resource) -> dict[str, bool]:
        """Get all effective permissions for a user on a resource.

        Returns:
            Dict mapping permission names to allowed (True) or denied (False).
        """
        raise NotImplementedError("PolicyEngine.get_all_permissions not yet implemented")
