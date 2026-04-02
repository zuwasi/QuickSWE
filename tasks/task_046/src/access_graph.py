"""Access graph for hierarchical permission resolution."""

from .principal import User, Group, Role
from .resource import Resource


class AccessGraph:
    """Graph-based access control system.

    Manages the relationships between Users, Groups, Roles, and Resources.
    Resolves effective permissions by traversing the hierarchy.

    Hierarchy:
        User -> Group (membership)
        Group -> Group (nesting)
        Group -> Role (assignment)
        User -> Role (direct assignment)
        Role -> Resource x Permission (grants/denies)
    """

    def __init__(self):
        self._users: dict[str, User] = {}
        self._groups: dict[str, Group] = {}
        self._roles: dict[str, Role] = {}
        self._resources: dict[str, Resource] = {}
        # Relationships — to be populated
        self._user_groups: dict[str, set[str]] = {}      # user_id -> set of group_ids
        self._group_children: dict[str, set[str]] = {}    # parent_group_id -> set of child_group_ids
        self._group_roles: dict[str, set[str]] = {}       # group_id -> set of role_ids
        self._user_roles: dict[str, set[str]] = {}        # user_id -> set of role_ids
        self._role_grants: dict[str, dict[str, set[str]]] = {}   # role_id -> {resource_id: {permissions}}
        self._role_denials: dict[str, dict[str, set[str]]] = {}  # role_id -> {resource_id: {permissions}}

    def add_user(self, user: User) -> None:
        self._users[user.id] = user

    def add_group(self, group: Group) -> None:
        self._groups[group.id] = group

    def add_role(self, role: Role) -> None:
        self._roles[role.id] = role

    def add_resource(self, resource: Resource) -> None:
        self._resources[resource.id] = resource

    def assign_user_to_group(self, user: User, group: Group) -> None:
        """Make user a member of group."""
        self._user_groups.setdefault(user.id, set()).add(group.id)

    def assign_group_to_group(self, child: Group, parent: Group) -> None:
        """Make child_group a sub-group of parent_group."""
        self._group_children.setdefault(parent.id, set()).add(child.id)

    def assign_role_to_group(self, role: Role, group: Group) -> None:
        """Assign a role to a group."""
        self._group_roles.setdefault(group.id, set()).add(role.id)

    def assign_role_to_user(self, role: Role, user: User) -> None:
        """Assign a role directly to a user."""
        self._user_roles.setdefault(user.id, set()).add(role.id)

    def grant_permission(self, role: Role, resource: Resource,
                         permission: str) -> None:
        """Grant a permission to a role on a resource."""
        self._role_grants.setdefault(role.id, {}).setdefault(
            resource.id, set()).add(permission)

    def deny_permission(self, role: Role, resource: Resource,
                        permission: str) -> None:
        """Explicitly deny a permission for a role on a resource."""
        self._role_denials.setdefault(role.id, {}).setdefault(
            resource.id, set()).add(permission)

    def resolve_permissions(self, user: User,
                            resource: Resource) -> dict[str, str]:
        """Resolve effective permissions for a user on a resource.

        Traverses the hierarchy to collect all grants and denials.
        Deny overrides allow.

        Args:
            user: The user to resolve permissions for.
            resource: The resource to check.

        Returns:
            Dict mapping permission name to "allow" or "deny".
            Only permissions that have been explicitly granted or denied
            are included.
        """
        raise NotImplementedError(
            "AccessGraph.resolve_permissions not yet implemented"
        )

    def get_user_roles(self, user: User) -> set[Role]:
        """Get all effective roles for a user (direct + via groups).

        Should traverse group hierarchy to find all roles.
        """
        raise NotImplementedError(
            "AccessGraph.get_user_roles not yet implemented"
        )

    def get_user_groups(self, user: User) -> set[Group]:
        """Get all groups a user belongs to (including nested parent groups).

        Should traverse the group hierarchy upward.
        """
        raise NotImplementedError(
            "AccessGraph.get_user_groups not yet implemented"
        )
