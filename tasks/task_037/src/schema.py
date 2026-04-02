"""
Schema definitions for data models.
Defines field types, constraints, and validation rules.
"""


class FieldType:
    """Enumeration of supported field types."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"


class Field:
    """Definition of a single field in a schema."""

    def __init__(self, name, field_type, required=True, max_length=None,
                 min_value=None, max_value=None, default=None):
        self.name = name
        self.field_type = field_type
        self.required = required
        self.max_length = max_length
        self.min_value = min_value
        self.max_value = max_value
        self.default = default

    def __repr__(self):
        constraints = []
        if self.required:
            constraints.append("required")
        if self.max_length is not None:
            constraints.append(f"max_length={self.max_length}")
        if self.min_value is not None:
            constraints.append(f"min={self.min_value}")
        if self.max_value is not None:
            constraints.append(f"max={self.max_value}")
        return f"Field({self.name!r}, {self.field_type}, {', '.join(constraints)})"


class Schema:
    """Defines the structure of a data record."""

    def __init__(self, name, fields=None):
        self.name = name
        self._fields = {}
        if fields:
            for field in fields:
                self.add_field(field)

    def add_field(self, field):
        """Add a field to the schema."""
        if not isinstance(field, Field):
            raise TypeError("Expected a Field instance")
        if field.name in self._fields:
            raise ValueError(f"Duplicate field name: {field.name}")
        self._fields[field.name] = field

    def get_field(self, name):
        """Get a field by name."""
        return self._fields.get(name)

    def get_fields(self):
        """Return all fields."""
        return list(self._fields.values())

    def get_required_fields(self):
        """Return required field names."""
        return [f.name for f in self._fields.values() if f.required]

    def has_field(self, name):
        """Check if field exists in schema."""
        return name in self._fields

    @property
    def field_names(self):
        return list(self._fields.keys())

    def __repr__(self):
        return f"Schema({self.name!r}, fields={self.field_names})"


# Pre-built schemas
USER_SCHEMA = Schema("user", [
    Field("id", FieldType.INTEGER, required=True),
    Field("username", FieldType.STRING, required=True, max_length=30),
    Field("full_name", FieldType.STRING, required=True, max_length=50),
    Field("email", FieldType.STRING, required=True, max_length=100),
    Field("bio", FieldType.STRING, required=False, max_length=200, default=""),
    Field("age", FieldType.INTEGER, required=False, min_value=0, max_value=150),
    Field("active", FieldType.BOOLEAN, required=False, default=True),
])

PRODUCT_SCHEMA = Schema("product", [
    Field("id", FieldType.INTEGER, required=True),
    Field("name", FieldType.STRING, required=True, max_length=100),
    Field("description", FieldType.STRING, required=False, max_length=500, default=""),
    Field("price", FieldType.FLOAT, required=True, min_value=0),
    Field("in_stock", FieldType.BOOLEAN, required=False, default=True),
])
