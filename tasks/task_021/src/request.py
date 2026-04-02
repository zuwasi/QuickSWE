"""Request and Response dataclasses for the HTTP-like framework."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Request:
    """Represents an incoming request."""
    method: str
    path: str
    headers: dict = field(default_factory=dict)
    body: Any = None

    def header(self, name: str, default: str = "") -> str:
        """Get a header value, case-insensitive."""
        for key, value in self.headers.items():
            if key.lower() == name.lower():
                return value
        return default


@dataclass
class Response:
    """Represents an outgoing response."""
    status_code: int
    body: Any = None
    headers: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300

    def set_header(self, name: str, value: str) -> None:
        self.headers[name] = value
