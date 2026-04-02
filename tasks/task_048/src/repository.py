"""Repository pattern for User entities."""

from .model import User
from .storage import InMemoryStorage


class UserRepository:
    """Repository for User CRUD operations.

    Every operation hits the storage backend directly.
    """

    def __init__(self, storage: InMemoryStorage):
        self._storage = storage

    def get_by_id(self, user_id: str) -> User | None:
        """Get a user by ID. Returns None if not found."""
        data = self._storage.get(user_id)
        if data is None:
            return None
        return User.from_dict(data)

    def get_all(self) -> list[User]:
        """Get all users."""
        return [User.from_dict(d) for d in self._storage.all()]

    def create(self, user: User) -> User:
        """Create a new user. Raises ValueError if ID already exists."""
        if self._storage.get(user.id) is not None:
            raise ValueError(f"User with id '{user.id}' already exists")
        self._storage.put(user.id, user.to_dict())
        return user

    def update(self, user: User) -> User:
        """Update an existing user. Raises ValueError if not found."""
        if self._storage.get(user.id) is None:
            raise ValueError(f"User with id '{user.id}' not found")
        self._storage.put(user.id, user.to_dict())
        return user

    def delete(self, user_id: str) -> bool:
        """Delete a user by ID. Returns True if existed."""
        return self._storage.delete(user_id)

    @property
    def storage(self) -> InMemoryStorage:
        """Access to underlying storage (for testing)."""
        return self._storage
