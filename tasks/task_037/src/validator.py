"""
Validator module for checking data against schema constraints.
Contains comprehensive validation including max_length checks.
"""

from .schema import FieldType


class ValidationError(Exception):
    """Raised when data fails validation."""

    def __init__(self, field_name, message, value=None):
        self.field_name = field_name
        self.message = message
        self.value = value
        super().__init__(f"Validation error on '{field_name}': {message}")


class Validator:
    """Validates data records against a schema."""

    def __init__(self, schema, strict=True):
        self.schema = schema
        self.strict = strict
        self._errors = []

    def validate(self, data):
        """Validate a data dict against the schema.

        Returns True if valid, False if not.
        Errors are stored in self._errors.
        """
        self._errors = []

        # Check for required fields
        for field_name in self.schema.get_required_fields():
            if field_name not in data:
                self._errors.append(
                    ValidationError(field_name, "Required field is missing")
                )

        # Check for unknown fields
        if self.strict:
            for key in data:
                if not self.schema.has_field(key):
                    self._errors.append(
                        ValidationError(key, "Unknown field")
                    )

        # Validate each field
        for field in self.schema.get_fields():
            if field.name not in data:
                continue
            value = data[field.name]
            self._validate_field(field, value)

        return len(self._errors) == 0

    def _validate_field(self, field, value):
        """Validate a single field value."""
        # Type checking
        if not self._check_type(field, value):
            self._errors.append(
                ValidationError(
                    field.name,
                    f"Expected type {field.field_type}, got {type(value).__name__}",
                    value,
                )
            )
            return

        # Max length check for strings
        if field.field_type == FieldType.STRING and field.max_length is not None:
            if len(value) > field.max_length:
                self._errors.append(
                    ValidationError(
                        field.name,
                        f"Value exceeds max length of {field.max_length} "
                        f"(got {len(value)} chars)",
                        value,
                    )
                )

        # Range checks for numbers
        if field.field_type in (FieldType.INTEGER, FieldType.FLOAT):
            if field.min_value is not None and value < field.min_value:
                self._errors.append(
                    ValidationError(
                        field.name,
                        f"Value {value} is below minimum {field.min_value}",
                        value,
                    )
                )
            if field.max_value is not None and value > field.max_value:
                self._errors.append(
                    ValidationError(
                        field.name,
                        f"Value {value} is above maximum {field.max_value}",
                        value,
                    )
                )

    def _check_type(self, field, value):
        """Check if value matches the expected field type."""
        type_map = {
            FieldType.STRING: str,
            FieldType.INTEGER: int,
            FieldType.FLOAT: (int, float),
            FieldType.BOOLEAN: bool,
            FieldType.LIST: list,
        }
        expected = type_map.get(field.field_type)
        if expected is None:
            return True
        # Special case: bool is a subclass of int in Python
        if field.field_type == FieldType.INTEGER and isinstance(value, bool):
            return False
        return isinstance(value, expected)

    @property
    def errors(self):
        return list(self._errors)

    def get_error_messages(self):
        return [str(e) for e in self._errors]
