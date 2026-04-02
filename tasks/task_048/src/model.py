"""User model for the repository pattern."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class User:
    """User entity."""
    id: str
    name: str
    email: str
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        created = data.get("created_at")
        if isinstance(created, str):
            created = datetime.fromisoformat(created)
        return cls(
            id=data["id"],
            name=data["name"],
            email=data["email"],
            created_at=created or datetime.now(),
        )

    def __eq__(self, other):
        if not isinstance(other, User):
            return NotImplemented
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)
