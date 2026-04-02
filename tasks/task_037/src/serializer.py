"""
Serializer module for converting data records to/from storage format.
Handles type coercion, defaults, and field serialization.
"""

from .schema import FieldType
from .validator import Validator


class SerializationError(Exception):
    """Raised when serialization fails."""
    pass


class Serializer:
    """Serializes and deserializes data records according to a schema."""

    def __init__(self, schema, validate_types=True):
        self.schema = schema
        self.validate_types = validate_types
        # Red herring: the validator IS instantiated and CAN check max_length
        self._validator = Validator(schema, strict=False)

    def serialize(self, data):
        """Serialize a data dict to storage format.

        Applies defaults, validates types, and serializes each field.
        """
        result = {}

        # Apply defaults for missing optional fields
        for field in self.schema.get_fields():
            if field.name not in data:
                if field.required:
                    raise SerializationError(
                        f"Missing required field: {field.name}"
                    )
                if field.default is not None:
                    result[field.name] = field.default
                continue

            value = data[field.name]

            # Type validation only — does NOT call self._validator.validate()
            # BUG: calls _serialize_field directly, which truncates but does
            # NOT raise on max_length violations
            if self.validate_types:
                self._check_type(field, value)

            result[field.name] = self._serialize_field(field, value)

        return result

    def _check_type(self, field, value):
        """Check that value matches field type. Raises on mismatch."""
        type_map = {
            FieldType.STRING: str,
            FieldType.INTEGER: int,
            FieldType.FLOAT: (int, float),
            FieldType.BOOLEAN: bool,
            FieldType.LIST: list,
        }
        expected = type_map.get(field.field_type)
        if expected is None:
            return
        if field.field_type == FieldType.INTEGER and isinstance(value, bool):
            raise SerializationError(
                f"Field '{field.name}': expected int, got bool"
            )
        if not isinstance(value, expected):
            raise SerializationError(
                f"Field '{field.name}': expected {field.field_type}, "
                f"got {type(value).__name__}"
            )

    def _serialize_field(self, field, value):
        """Serialize a single field value to storage format.

        BUG: silently truncates strings to max_length instead of raising.
        The caller never knows data was lost.
        """
        if field.field_type == FieldType.STRING:
            value = str(value)
            # SILENT TRUNCATION — this is the bug
            if field.max_length is not None:
                value = value[:field.max_length]
            return value

        if field.field_type == FieldType.INTEGER:
            return int(value)

        if field.field_type == FieldType.FLOAT:
            return float(value)

        if field.field_type == FieldType.BOOLEAN:
            return bool(value)

        if field.field_type == FieldType.LIST:
            return list(value)

        return value

    def deserialize(self, stored_data):
        """Deserialize stored data back to a dict."""
        result = {}
        for field in self.schema.get_fields():
            if field.name in stored_data:
                result[field.name] = stored_data[field.name]
            elif field.default is not None:
                result[field.name] = field.default
        return result

    def validate_and_serialize(self, data):
        """Validate using full validator, then serialize.

        NOTE: This method correctly validates max_length, but the
        plain serialize() method is what's actually called in the
        Store class below — so this safer path is never used.
        """
        if not self._validator.validate(data):
            errors = self._validator.get_error_messages()
            raise SerializationError(
                f"Validation failed: {'; '.join(errors)}"
            )
        return self.serialize(data)
