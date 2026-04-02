import sys
import os
import time
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.user_manager import UserManager


# ── pass-to-pass: UserManager public API ────────────────────────────

class TestUserManagerCRUD:
    def setup_method(self):
        self.mgr = UserManager()

    def test_create_user(self):
        u = self.mgr.create_user("alice", "alice@example.com", "secret123")
        assert u["username"] == "alice"
        assert u["email"] == "alice@example.com"
        assert "id" in u

    def test_get_user(self):
        u = self.mgr.create_user("bob", "bob@example.com", "pass1234")
        fetched = self.mgr.get_user(u["id"])
        assert fetched["username"] == "bob"

    def test_get_user_not_found(self):
        assert self.mgr.get_user("nonexistent") is None

    def test_get_user_by_username(self):
        self.mgr.create_user("carol", "carol@example.com", "pass1234")
        u = self.mgr.get_user_by_username("carol")
        assert u is not None
        assert u["email"] == "carol@example.com"

    def test_update_user(self):
        u = self.mgr.create_user("dave", "dave@example.com", "pass1234")
        updated = self.mgr.update_user(u["id"], email="dave2@example.com")
        assert updated["email"] == "dave2@example.com"

    def test_update_user_bad_field(self):
        u = self.mgr.create_user("eve", "eve@example.com", "pass1234")
        with pytest.raises(ValueError):
            self.mgr.update_user(u["id"], password_hash="hacked")

    def test_delete_user(self):
        u = self.mgr.create_user("frank", "frank@example.com", "pass1234")
        self.mgr.delete_user(u["id"])
        assert self.mgr.get_user(u["id"]) is None

    def test_delete_user_not_found(self):
        with pytest.raises(KeyError):
            self.mgr.delete_user("ghost")

    def test_list_users(self):
        self.mgr.create_user("a1", "a1@x.com", "pass1234")
        self.mgr.create_user("a2", "a2@x.com", "pass1234")
        assert len(self.mgr.list_users()) == 2

    def test_duplicate_username(self):
        self.mgr.create_user("dup", "dup1@x.com", "pass1234")
        with pytest.raises(ValueError):
            self.mgr.create_user("dup", "dup2@x.com", "pass1234")

    def test_duplicate_email(self):
        self.mgr.create_user("u1", "same@x.com", "pass1234")
        with pytest.raises(ValueError):
            self.mgr.create_user("u2", "same@x.com", "pass1234")


class TestUserManagerAuth:
    def setup_method(self):
        self.mgr = UserManager()
        self.user = self.mgr.create_user("tester", "t@x.com", "MyP@ss99")

    def test_authenticate_success(self):
        token = self.mgr.authenticate("tester", "MyP@ss99")
        assert token is not None

    def test_authenticate_wrong_password(self):
        assert self.mgr.authenticate("tester", "wrong") is None

    def test_authenticate_unknown_user(self):
        assert self.mgr.authenticate("nobody", "pass") is None

    def test_authenticate_inactive_user(self):
        self.mgr.update_user(self.user["id"], active=False)
        assert self.mgr.authenticate("tester", "MyP@ss99") is None

    def test_change_password(self):
        self.mgr.change_password(self.user["id"], "MyP@ss99", "NewP@ss11")
        token = self.mgr.authenticate("tester", "NewP@ss11")
        assert token is not None

    def test_change_password_wrong_old(self):
        with pytest.raises(PermissionError):
            self.mgr.change_password(self.user["id"], "bad", "NewP@ss11")

    def test_change_password_too_short(self):
        with pytest.raises(ValueError):
            self.mgr.change_password(self.user["id"], "MyP@ss99", "abc")


class TestUserManagerSessions:
    def setup_method(self):
        self.mgr = UserManager()
        self.user = self.mgr.create_user("sess_user", "s@x.com", "pass1234")

    def test_create_and_validate_session(self):
        token = self.mgr.create_session(self.user["id"])
        uid = self.mgr.validate_session(token)
        assert uid == self.user["id"]

    def test_validate_bad_token(self):
        assert self.mgr.validate_session("fake") is None

    def test_destroy_session(self):
        token = self.mgr.create_session(self.user["id"])
        assert self.mgr.destroy_session(token) is True
        assert self.mgr.validate_session(token) is None

    def test_destroy_nonexistent(self):
        assert self.mgr.destroy_session("nope") is False

    def test_delete_user_cleans_sessions(self):
        token = self.mgr.create_session(self.user["id"])
        self.mgr.delete_user(self.user["id"])
        assert self.mgr.validate_session(token) is None


class TestUserManagerEmails:
    def setup_method(self):
        self.mgr = UserManager()

    def test_welcome_email_on_create(self):
        self.mgr.create_user("mail_u", "mail@x.com", "pass1234")
        log = self.mgr.get_email_log()
        assert len(log) == 1
        assert log[0]["type"] == "welcome"

    def test_password_reset_email(self):
        tok = self.mgr.send_password_reset_email("x@x.com")
        assert isinstance(tok, str) and len(tok) > 0


# ── fail-to-pass: component classes must exist ──────────────────────

class TestComponentClasses:
    @pytest.mark.fail_to_pass
    def test_user_repository_importable(self):
        from src.user_manager import UserRepository
        repo = UserRepository()
        assert hasattr(repo, "create_user")
        assert hasattr(repo, "get_user")
        assert hasattr(repo, "delete_user")
        assert hasattr(repo, "list_users")

    @pytest.mark.fail_to_pass
    def test_user_repository_crud(self):
        from src.user_manager import UserRepository
        repo = UserRepository()
        uid = repo.create_user("alice", "a@x.com", "hash123")
        assert repo.get_user(uid) is not None
        repo.delete_user(uid)
        assert repo.get_user(uid) is None

    @pytest.mark.fail_to_pass
    def test_auth_service_importable(self):
        from src.user_manager import AuthService, UserRepository
        repo = UserRepository()
        auth = AuthService(repo)
        assert hasattr(auth, "authenticate")
        assert hasattr(auth, "hash_password")
        assert hasattr(auth, "verify_password")

    @pytest.mark.fail_to_pass
    def test_auth_service_hash_and_verify(self):
        from src.user_manager import AuthService, UserRepository
        repo = UserRepository()
        auth = AuthService(repo)
        h = auth.hash_password("secret")
        assert auth.verify_password("secret", h) is True
        assert auth.verify_password("wrong", h) is False

    @pytest.mark.fail_to_pass
    def test_session_manager_importable(self):
        from src.user_manager import SessionManager
        sm = SessionManager()
        assert hasattr(sm, "create_session")
        assert hasattr(sm, "validate_session")
        assert hasattr(sm, "destroy_session")

    @pytest.mark.fail_to_pass
    def test_session_manager_lifecycle(self):
        from src.user_manager import SessionManager
        sm = SessionManager()
        tok = sm.create_session("user_42")
        assert sm.validate_session(tok) == "user_42"
        sm.destroy_session(tok)
        assert sm.validate_session(tok) is None
