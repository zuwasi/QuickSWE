"""Resource classes for access control."""

from dataclasses import dataclass


@dataclass
class Resource:
    """A resource that can have permissions assigned."""
    id: str
    name: str
    resource_type: str = "generic"

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if not isinstance(other, Resource):
            return NotImplemented
        return self.id == other.id


# Standard permission types
PERMISSIONS = {"read", "write", "delete", "admin"}
