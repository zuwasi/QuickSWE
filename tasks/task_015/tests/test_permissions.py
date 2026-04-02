import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.permissions import check_access


# ── helpers ─────────────────────────────────────────────────────────

def _user(role="viewer", active=True, uid="u1", dept="engineering"):
    return {"id": uid, "role": role, "active": active, "department": dept}

def _resource(rtype="public", owner="u1", dept="engineering"):
    return {"id": "r1", "type": rtype, "owner_id": owner, "department": dept}


# ── pass-to-pass: check_access behaviour ───────────────────────────

class TestAdminAccess:
    def test_admin_read_public(self):
        assert check_access(_user("admin"), _resource("public"), "read") == "allow"

    def test_admin_delete_confidential(self):
        assert check_access(_user("admin"), _resource("confidential"), "delete") == "allow"

    def test_admin_write_internal(self):
        assert check_access(_user("admin"), _resource("internal"), "write") == "allow"


class TestInactiveUser:
    def test_inactive_denied(self):
        assert check_access(_user(active=False), _resource("public"), "read") == "deny"


class TestPublicResource:
    def test_viewer_read_public(self):
        assert check_access(_user("viewer"), _resource("public"), "read") == "allow"

    def test_viewer_write_public(self):
        assert check_access(_user("viewer"), _resource("public"), "write") == "deny"

    def test_editor_write_public(self):
        assert check_access(_user("editor"), _resource("public"), "write") == "allow"

    def test_editor_delete_public(self):
        assert check_access(_user("editor"), _resource("public"), "delete") == "deny"

    def test_guest_read_public(self):
        assert check_access(_user("guest"), _resource("public"), "read") == "allow"


class TestInternalResource:
    def test_same_dept_read(self):
        assert check_access(
            _user("viewer", dept="eng"), _resource("internal", dept="eng"), "read"
        ) == "allow"

    def test_diff_dept_read(self):
        assert check_access(
            _user("viewer", dept="eng"), _resource("internal", dept="hr"), "read"
        ) == "deny"

    def test_editor_same_dept_write(self):
        assert check_access(
            _user("editor", dept="eng"), _resource("internal", dept="eng"), "write"
        ) == "allow"

    def test_editor_same_dept_delete(self):
        assert check_access(
            _user("editor", dept="eng"), _resource("internal", dept="eng"), "delete"
        ) == "deny"

    def test_owner_write_internal(self):
        assert check_access(
            _user("viewer", uid="u5", dept="eng"),
            _resource("internal", owner="u5", dept="eng"),
            "write",
        ) == "allow"

    def test_owner_delete_internal(self):
        assert check_access(
            _user("viewer", uid="u5", dept="eng"),
            _resource("internal", owner="u5", dept="eng"),
            "delete",
        ) == "deny"

    def test_non_owner_viewer_write(self):
        assert check_access(
            _user("viewer", uid="u5", dept="eng"),
            _resource("internal", owner="u9", dept="eng"),
            "write",
        ) == "deny"


class TestConfidentialResource:
    def test_owner_read(self):
        assert check_access(
            _user("viewer", uid="u1"), _resource("confidential", owner="u1"), "read"
        ) == "allow"

    def test_owner_write(self):
        assert check_access(
            _user("viewer", uid="u1"), _resource("confidential", owner="u1"), "write"
        ) == "allow"

    def test_owner_delete(self):
        assert check_access(
            _user("viewer", uid="u1"), _resource("confidential", owner="u1"), "delete"
        ) == "deny"

    def test_editor_same_dept_read(self):
        assert check_access(
            _user("editor", uid="u2", dept="eng"),
            _resource("confidential", owner="u1", dept="eng"),
            "read",
        ) == "allow"

    def test_editor_same_dept_write(self):
        assert check_access(
            _user("editor", uid="u2", dept="eng"),
            _resource("confidential", owner="u1", dept="eng"),
            "write",
        ) == "deny"

    def test_viewer_diff_dept(self):
        assert check_access(
            _user("viewer", uid="u3", dept="hr"),
            _resource("confidential", owner="u1", dept="eng"),
            "read",
        ) == "deny"


class TestErrorCases:
    def test_none_user(self):
        assert check_access(None, _resource(), "read") == "error"

    def test_none_resource(self):
        assert check_access(_user(), None, "read") == "error"

    def test_none_action(self):
        assert check_access(_user(), _resource(), None) == "error"

    def test_non_dict_user(self):
        assert check_access("not_a_dict", _resource(), "read") == "error"

    def test_unknown_resource_type(self):
        assert check_access(_user(), _resource("secret"), "read") == "deny"


# ── fail-to-pass: can_access wrapper must exist ────────────────────

class TestCanAccessWrapper:
    @pytest.mark.fail_to_pass
    def test_can_access_importable(self):
        from src.permissions import can_access
        assert callable(can_access)

    @pytest.mark.fail_to_pass
    def test_can_access_returns_bool_true(self):
        from src.permissions import can_access
        result = can_access(_user("admin"), _resource("public"), "read")
        assert result is True

    @pytest.mark.fail_to_pass
    def test_can_access_returns_bool_false(self):
        from src.permissions import can_access
        result = can_access(_user("viewer"), _resource("public"), "write")
        assert result is False

    @pytest.mark.fail_to_pass
    def test_can_access_error_returns_false(self):
        from src.permissions import can_access
        result = can_access(None, _resource(), "read")
        assert result is False

    @pytest.mark.fail_to_pass
    def test_can_access_owner_confidential(self):
        from src.permissions import can_access
        result = can_access(
            _user("viewer", uid="u1"), _resource("confidential", owner="u1"), "read"
        )
        assert result is True

    @pytest.mark.fail_to_pass
    def test_can_access_non_owner_confidential(self):
        from src.permissions import can_access
        result = can_access(
            _user("viewer", uid="u3", dept="hr"),
            _resource("confidential", owner="u1", dept="eng"),
            "read",
        )
        assert result is False
