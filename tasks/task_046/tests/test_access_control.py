import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.principal import User, Group, Role
from src.resource import Resource
from src.access_graph import AccessGraph
from src.policy import PolicyEngine


# ── pass-to-pass: basic entity operations ──────────────────────────


class TestEntityBasics:
    def test_user_creation(self):
        u = User(id="u1", name="Alice")
        assert u.id == "u1"
        assert u.name == "Alice"

    def test_user_equality(self):
        assert User("u1", "Alice") == User("u1", "Alice")
        assert User("u1", "Alice") != User("u2", "Bob")

    def test_group_creation(self):
        g = Group(id="g1", name="Engineering")
        assert g.id == "g1"

    def test_role_creation(self):
        r = Role(id="r1", name="Editor")
        assert r.id == "r1"

    def test_resource_creation(self):
        res = Resource(id="res1", name="Document", resource_type="file")
        assert res.id == "res1"
        assert res.resource_type == "file"

    def test_user_hash(self):
        u1 = User("u1", "Alice")
        u2 = User("u1", "Alice")
        assert hash(u1) == hash(u2)
        s = {u1, u2}
        assert len(s) == 1


class TestAccessGraphSetup:
    def test_add_entities(self):
        graph = AccessGraph()
        graph.add_user(User("u1", "Alice"))
        graph.add_group(Group("g1", "Eng"))
        graph.add_role(Role("r1", "Reader"))
        graph.add_resource(Resource("res1", "Doc"))

    def test_assign_user_to_group(self):
        graph = AccessGraph()
        u = User("u1", "Alice")
        g = Group("g1", "Eng")
        graph.add_user(u)
        graph.add_group(g)
        graph.assign_user_to_group(u, g)

    def test_grant_permission(self):
        graph = AccessGraph()
        r = Role("r1", "Reader")
        res = Resource("res1", "Doc")
        graph.add_role(r)
        graph.add_resource(res)
        graph.grant_permission(r, res, "read")

    def test_deny_permission(self):
        graph = AccessGraph()
        r = Role("r1", "Restricted")
        res = Resource("res1", "Secret")
        graph.add_role(r)
        graph.add_resource(res)
        graph.deny_permission(r, res, "write")


# ── fail-to-pass: permission resolution ──────────────────────────


class TestDirectRolePermissions:
    @pytest.mark.fail_to_pass
    def test_direct_role_grant(self):
        """User with direct role gets that role's permissions."""
        graph = AccessGraph()
        user = User("u1", "Alice")
        role = Role("r1", "Reader")
        res = Resource("res1", "Document")
        graph.add_user(user)
        graph.add_role(role)
        graph.add_resource(res)
        graph.assign_role_to_user(role, user)
        graph.grant_permission(role, res, "read")

        perms = graph.resolve_permissions(user, res)
        assert perms.get("read") == "allow"

    @pytest.mark.fail_to_pass
    def test_no_role_no_permissions(self):
        """User with no roles has no permissions."""
        graph = AccessGraph()
        user = User("u1", "Alice")
        res = Resource("res1", "Document")
        graph.add_user(user)
        graph.add_resource(res)

        perms = graph.resolve_permissions(user, res)
        assert perms == {}

    @pytest.mark.fail_to_pass
    def test_multiple_permissions(self):
        """Role with multiple permissions grants all of them."""
        graph = AccessGraph()
        user = User("u1", "Alice")
        role = Role("r1", "Admin")
        res = Resource("res1", "System")
        graph.add_user(user)
        graph.add_role(role)
        graph.add_resource(res)
        graph.assign_role_to_user(role, user)
        graph.grant_permission(role, res, "read")
        graph.grant_permission(role, res, "write")
        graph.grant_permission(role, res, "admin")

        perms = graph.resolve_permissions(user, res)
        assert perms.get("read") == "allow"
        assert perms.get("write") == "allow"
        assert perms.get("admin") == "allow"


class TestGroupInheritance:
    @pytest.mark.fail_to_pass
    def test_group_role_inherited(self):
        """User inherits permissions from group's role."""
        graph = AccessGraph()
        user = User("u1", "Alice")
        group = Group("g1", "Engineering")
        role = Role("r1", "Developer")
        res = Resource("res1", "Repo")
        graph.add_user(user)
        graph.add_group(group)
        graph.add_role(role)
        graph.add_resource(res)
        graph.assign_user_to_group(user, group)
        graph.assign_role_to_group(role, group)
        graph.grant_permission(role, res, "write")

        perms = graph.resolve_permissions(user, res)
        assert perms.get("write") == "allow"

    @pytest.mark.fail_to_pass
    def test_nested_group_inheritance(self):
        """User inherits permissions through nested group chain."""
        graph = AccessGraph()
        user = User("u1", "Alice")
        team = Group("g1", "Backend Team")
        eng = Group("g2", "Engineering")
        role = Role("r1", "AllAccess")
        res = Resource("res1", "Server")
        graph.add_user(user)
        graph.add_group(team)
        graph.add_group(eng)
        graph.add_role(role)
        graph.add_resource(res)
        # Alice -> Backend Team -> Engineering -> AllAccess
        graph.assign_user_to_group(user, team)
        graph.assign_group_to_group(team, eng)
        graph.assign_role_to_group(role, eng)
        graph.grant_permission(role, res, "admin")

        perms = graph.resolve_permissions(user, res)
        assert perms.get("admin") == "allow"

    @pytest.mark.fail_to_pass
    def test_get_user_roles(self):
        """get_user_roles returns all direct and inherited roles."""
        graph = AccessGraph()
        user = User("u1", "Alice")
        group = Group("g1", "Eng")
        direct_role = Role("r1", "Direct")
        group_role = Role("r2", "GroupRole")
        graph.add_user(user)
        graph.add_group(group)
        graph.add_role(direct_role)
        graph.add_role(group_role)
        graph.assign_role_to_user(direct_role, user)
        graph.assign_user_to_group(user, group)
        graph.assign_role_to_group(group_role, group)

        roles = graph.get_user_roles(user)
        role_ids = {r.id for r in roles}
        assert "r1" in role_ids
        assert "r2" in role_ids


class TestDenyOverrides:
    @pytest.mark.fail_to_pass
    def test_deny_overrides_allow(self):
        """Explicit deny overrides allow from another role."""
        graph = AccessGraph()
        user = User("u1", "Alice")
        allow_role = Role("r1", "Writer")
        deny_role = Role("r2", "Restricted")
        res = Resource("res1", "Secret")
        graph.add_user(user)
        graph.add_role(allow_role)
        graph.add_role(deny_role)
        graph.add_resource(res)
        graph.assign_role_to_user(allow_role, user)
        graph.assign_role_to_user(deny_role, user)
        graph.grant_permission(allow_role, res, "write")
        graph.deny_permission(deny_role, res, "write")

        perms = graph.resolve_permissions(user, res)
        assert perms.get("write") == "deny"

    @pytest.mark.fail_to_pass
    def test_deny_from_group_overrides_direct_allow(self):
        """Deny from group role overrides direct role allow."""
        graph = AccessGraph()
        user = User("u1", "Alice")
        group = Group("g1", "Compliance")
        direct_role = Role("r1", "Editor")
        group_deny_role = Role("r2", "NoDelete")
        res = Resource("res1", "Audit Log")
        graph.add_user(user)
        graph.add_group(group)
        graph.add_role(direct_role)
        graph.add_role(group_deny_role)
        graph.add_resource(res)
        graph.assign_role_to_user(direct_role, user)
        graph.assign_user_to_group(user, group)
        graph.assign_role_to_group(group_deny_role, group)
        graph.grant_permission(direct_role, res, "delete")
        graph.deny_permission(group_deny_role, res, "delete")

        perms = graph.resolve_permissions(user, res)
        assert perms.get("delete") == "deny"


class TestPolicyEngine:
    @pytest.mark.fail_to_pass
    def test_check_access_allowed(self):
        """PolicyEngine.check_access returns True when allowed."""
        graph = AccessGraph()
        user = User("u1", "Alice")
        role = Role("r1", "Reader")
        res = Resource("res1", "Doc")
        graph.add_user(user)
        graph.add_role(role)
        graph.add_resource(res)
        graph.assign_role_to_user(role, user)
        graph.grant_permission(role, res, "read")

        engine = PolicyEngine(graph)
        assert engine.check_access(user, res, "read") is True

    @pytest.mark.fail_to_pass
    def test_check_access_denied(self):
        """PolicyEngine.check_access returns False when denied or no permission."""
        graph = AccessGraph()
        user = User("u1", "Alice")
        res = Resource("res1", "Doc")
        graph.add_user(user)
        graph.add_resource(res)

        engine = PolicyEngine(graph)
        assert engine.check_access(user, res, "write") is False

    @pytest.mark.fail_to_pass
    def test_circular_groups_no_infinite_loop(self):
        """Circular group membership should not cause infinite loop."""
        graph = AccessGraph()
        user = User("u1", "Alice")
        g1 = Group("g1", "GroupA")
        g2 = Group("g2", "GroupB")
        role = Role("r1", "Reader")
        res = Resource("res1", "Doc")
        graph.add_user(user)
        graph.add_group(g1)
        graph.add_group(g2)
        graph.add_role(role)
        graph.add_resource(res)
        # Circular: g1 -> g2 -> g1
        graph.assign_group_to_group(g1, g2)
        graph.assign_group_to_group(g2, g1)
        graph.assign_user_to_group(user, g1)
        graph.assign_role_to_group(role, g2)
        graph.grant_permission(role, res, "read")

        # Should terminate and resolve
        perms = graph.resolve_permissions(user, res)
        assert perms.get("read") == "allow"
