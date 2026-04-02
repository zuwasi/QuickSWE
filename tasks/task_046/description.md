# Feature Request: Graph-Based Access Control System

## Summary

Implement a hierarchical access control system where Users belong to Groups, Groups have Roles, and Roles have Permissions on Resources. An AccessGraph should resolve effective permissions by traversing the hierarchy. Support permission inheritance and explicit deny overrides.

## Current State

- `src/principal.py`: `User`, `Group`, `Role` classes with basic attributes but no hierarchy logic.
- `src/resource.py`: `Resource` class with name and type.
- `src/policy.py`: `PolicyEngine` stub — `check_access()` raises `NotImplementedError`.
- `src/access_graph.py`: `AccessGraph` stub — `resolve_permissions()` raises `NotImplementedError`.

## Requirements

### Hierarchy
- Users can be members of multiple Groups.
- Groups can contain sub-Groups (nested groups).
- Groups can have multiple Roles assigned.
- Roles define Permissions (allow/deny) on Resources.

### Permission Resolution (`AccessGraph`)
1. `add_user(user)`, `add_group(group)`, `add_role(role)`, `add_resource(resource)`.
2. `assign_user_to_group(user, group)` — user becomes member of group.
3. `assign_group_to_group(child_group, parent_group)` — nested groups.
4. `assign_role_to_group(role, group)` — group gets a role.
5. `assign_role_to_user(role, user)` — direct role assignment to user.
6. `grant_permission(role, resource, permission)` — allow a permission.
7. `deny_permission(role, resource, permission)` — explicit deny.
8. `resolve_permissions(user, resource) -> dict` — compute effective permissions.

### Resolution Rules
- A user's effective permissions = direct role permissions + all group role permissions (including nested groups).
- **Deny overrides allow**: If any role in the hierarchy denies a permission, the result is deny — even if other roles allow it.
- Permissions: `read`, `write`, `delete`, `admin`.

### PolicyEngine
- `check_access(user, resource, permission) -> bool` — uses AccessGraph to determine if access is allowed.

## Edge Cases
- Circular group membership should not cause infinite loops.
- User with no roles/groups has no permissions.
- Multiple paths to the same permission (via different groups) should resolve correctly.
