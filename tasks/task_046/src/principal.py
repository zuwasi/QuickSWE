"""Principal classes: User, Group, Role."""

from dataclasses import dataclass, field


@dataclass
class User:
    """A user principal."""
    id: str
    name: str

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if not isinstance(other, User):
            return NotImplemented
        return self.id == other.id


@dataclass
class Group:
    """A group that can contain users and sub-groups."""
    id: str
    name: str

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if not isinstance(other, Group):
            return NotImplemented
        return self.id == other.id


@dataclass
class Role:
    """A role that defines permissions on resources."""
    id: str
    name: str

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if not isinstance(other, Role):
            return NotImplemented
        return self.id == other.id
