"""Authentication middleware using simplified JWT tokens."""

import hashlib
import json
import time
import base64

from .middleware import Middleware, Response


class User:
    """Represents an authenticated user."""

    def __init__(self, user_id, username, tenant_id, roles=None):
        self.user_id = user_id
        self.username = username
        self.tenant_id = tenant_id
        self.roles = roles or []

    def has_role(self, role):
        return role in self.roles

    def is_admin(self):
        return 'admin' in self.roles

    def __repr__(self):
        return f"User(id={self.user_id}, username='{self.username}', tenant='{self.tenant_id}')"


class TokenEncoder:
    """Simple token encoder/decoder (simplified JWT for demo purposes)."""

    def __init__(self, secret='default-secret-key'):
        self._secret = secret

    def encode(self, payload):
        """Encode a payload into a token."""
        payload_copy = dict(payload)
        if 'iat' not in payload_copy:
            payload_copy['iat'] = int(time.time())
        if 'exp' not in payload_copy:
            payload_copy['exp'] = int(time.time()) + 3600

        payload_json = json.dumps(payload_copy, sort_keys=True)
        payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode()

        signature_input = f"{payload_b64}.{self._secret}"
        signature = hashlib.sha256(signature_input.encode()).hexdigest()[:32]

        return f"{payload_b64}.{signature}"

    def decode(self, token):
        """Decode and verify a token."""
        parts = token.split('.')
        if len(parts) != 2:
            raise ValueError("Invalid token format")

        payload_b64, signature = parts

        # Verify signature
        expected_sig_input = f"{payload_b64}.{self._secret}"
        expected_sig = hashlib.sha256(expected_sig_input.encode()).hexdigest()[:32]

        if signature != expected_sig:
            raise ValueError("Invalid token signature")

        # Decode payload
        try:
            payload_json = base64.urlsafe_b64decode(payload_b64.encode()).decode()
            payload = json.loads(payload_json)
        except Exception as e:
            raise ValueError(f"Invalid token payload: {e}")

        # Check expiration
        if 'exp' in payload and payload['exp'] < time.time():
            raise ValueError("Token expired")

        return payload


class AuthMiddleware(Middleware):
    """Authenticates requests using Bearer tokens.

    Sets request.user if authentication is successful.
    Allows unauthenticated requests to pass through (for public endpoints).
    """

    def __init__(self, secret='default-secret-key', required=False, name=None):
        super().__init__(name=name or "AuthMiddleware")
        self._encoder = TokenEncoder(secret)
        self._required = required
        self._auth_count = 0
        self._fail_count = 0

    @property
    def auth_count(self):
        return self._auth_count

    @property
    def fail_count(self):
        return self._fail_count

    def create_token(self, user_id, username, tenant_id, roles=None):
        """Helper to create a token for testing."""
        return self._encoder.encode({
            'user_id': user_id,
            'username': username,
            'tenant_id': tenant_id,
            'roles': roles or [],
        })

    def before_request(self, request):
        """Extract and verify the auth token, set request.user."""
        auth_header = request.headers.get('Authorization', '')

        if not auth_header.startswith('Bearer '):
            if self._required:
                self._fail_count += 1
                return Response(status=401, body={'error': 'Authentication required'})
            return None

        token = auth_header[7:]  # Strip "Bearer "

        try:
            payload = self._encoder.decode(token)
            request.user = User(
                user_id=payload['user_id'],
                username=payload['username'],
                tenant_id=payload['tenant_id'],
                roles=payload.get('roles', []),
            )
            self._auth_count += 1
        except ValueError as e:
            self._fail_count += 1
            if self._required:
                return Response(status=401, body={'error': str(e)})
            # Non-required auth: just don't set user

        return None
