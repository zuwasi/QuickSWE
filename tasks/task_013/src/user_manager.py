"""Monolithic user-management module — the classic god class."""

import hashlib
import time
import uuid


class UserManager:
    """Handles users, auth, sessions, emails — everything in one place."""

    def __init__(self):
        self._users = {}          # user_id -> user dict
        self._sessions = {}       # session_token -> session dict
        self._email_log = []      # list of "sent" emails (stub)

    # ── user CRUD ──────────────────────────────────────────────────

    def create_user(self, username, email, password):
        """Create a new user and return the user dict."""
        for u in self._users.values():
            if u["username"] == username:
                raise ValueError(f"Username '{username}' already taken")
            if u["email"] == email:
                raise ValueError(f"Email '{email}' already registered")

        user_id = str(uuid.uuid4())
        hashed = self._hash_password(password)
        user = {
            "id": user_id,
            "username": username,
            "email": email,
            "password_hash": hashed,
            "created_at": time.time(),
            "active": True,
        }
        self._users[user_id] = user
        self.send_welcome_email(email, username)
        return dict(user)

    def get_user(self, user_id):
        """Retrieve a user by ID.  Returns None if not found."""
        user = self._users.get(user_id)
        if user is None:
            return None
        return dict(user)

    def get_user_by_username(self, username):
        """Look up a user by username."""
        for u in self._users.values():
            if u["username"] == username:
                return dict(u)
        return None

    def update_user(self, user_id, **fields):
        """Update allowed fields on a user record."""
        if user_id not in self._users:
            raise KeyError(f"User '{user_id}' not found")
        allowed = {"username", "email", "active"}
        for key in fields:
            if key not in allowed:
                raise ValueError(f"Cannot update field '{key}'")
        self._users[user_id].update(fields)
        return dict(self._users[user_id])

    def delete_user(self, user_id):
        """Remove a user and all their sessions."""
        if user_id not in self._users:
            raise KeyError(f"User '{user_id}' not found")
        del self._users[user_id]
        # also kill any active sessions for this user
        tokens_to_remove = [
            tok for tok, s in self._sessions.items() if s["user_id"] == user_id
        ]
        for tok in tokens_to_remove:
            del self._sessions[tok]

    def list_users(self):
        """Return all users as a list of dicts."""
        return [dict(u) for u in self._users.values()]

    # ── authentication ─────────────────────────────────────────────

    def authenticate(self, username, password):
        """Authenticate a user. Returns a session token or None."""
        user = self.get_user_by_username(username)
        if user is None:
            return None
        if not user["active"]:
            return None
        if not self._verify_password(password, user["password_hash"]):
            return None
        token = self.create_session(user["id"])
        return token

    def change_password(self, user_id, old_password, new_password):
        """Change a user's password after verifying the old one."""
        if user_id not in self._users:
            raise KeyError(f"User '{user_id}' not found")
        user = self._users[user_id]
        if not self._verify_password(old_password, user["password_hash"]):
            raise PermissionError("Old password is incorrect")
        if len(new_password) < 6:
            raise ValueError("New password must be at least 6 characters")
        user["password_hash"] = self._hash_password(new_password)

    # ── password hashing (simplified) ──────────────────────────────

    def _hash_password(self, password):
        """Hash a password with a deterministic salt for demo purposes."""
        salted = "s4lt_" + password
        return hashlib.sha256(salted.encode()).hexdigest()

    def _verify_password(self, password, password_hash):
        """Verify a password against a stored hash."""
        return self._hash_password(password) == password_hash

    # ── session management ─────────────────────────────────────────

    def create_session(self, user_id, ttl=3600):
        """Create a session token for a user."""
        token = uuid.uuid4().hex
        self._sessions[token] = {
            "user_id": user_id,
            "created_at": time.time(),
            "expires_at": time.time() + ttl,
        }
        return token

    def validate_session(self, token):
        """Validate a session token. Returns user_id or None."""
        session = self._sessions.get(token)
        if session is None:
            return None
        if time.time() > session["expires_at"]:
            del self._sessions[token]
            return None
        return session["user_id"]

    def destroy_session(self, token):
        """Remove a session."""
        if token in self._sessions:
            del self._sessions[token]
            return True
        return False

    def cleanup_expired_sessions(self):
        """Remove all expired sessions. Returns count removed."""
        now = time.time()
        expired = [t for t, s in self._sessions.items() if now > s["expires_at"]]
        for t in expired:
            del self._sessions[t]
        return len(expired)

    # ── email sending (stubs) ──────────────────────────────────────

    def send_welcome_email(self, email, username):
        """Stub: record a welcome email."""
        self._email_log.append({
            "type": "welcome",
            "to": email,
            "body": f"Welcome, {username}!",
        })

    def send_password_reset_email(self, email):
        """Stub: record a password-reset email."""
        reset_token = uuid.uuid4().hex[:8]
        self._email_log.append({
            "type": "password_reset",
            "to": email,
            "token": reset_token,
        })
        return reset_token

    def get_email_log(self):
        """Return all sent emails (for testing)."""
        return list(self._email_log)
