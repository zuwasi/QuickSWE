"""Serializer for pipeline results.

RED HERRING: This module has intentionally suspicious-looking type checking
and conversion logic, but it is actually correct. The data corruption bug
is NOT here.
"""

import json
from datetime import datetime, date


class PipelineSerializer:
    """Serializes pipeline results to various formats.

    The type-checking logic below looks complex and potentially buggy,
    but it correctly handles all edge cases for serialization.
    """

    SUPPORTED_FORMATS = ('json', 'csv', 'dict')

    def __init__(self, format='json', strict_types=False):
        if format not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {format}")
        self._format = format
        self._strict_types = strict_types
        self._type_coercions = {}
        self._custom_serializers = {}
        self._warnings = []

    def register_type(self, type_class, serializer_fn):
        """Register a custom serializer for a type."""
        self._custom_serializers[type_class] = serializer_fn

    def _coerce_value(self, value):
        """Coerce a value to a serializable type.

        This looks suspicious because it modifies types, but it only
        creates NEW objects — never mutates the originals.
        """
        if value is None:
            return None

        # Check custom serializers first
        for type_class, serializer_fn in self._custom_serializers.items():
            if isinstance(value, type_class):
                return serializer_fn(value)

        # Handle datetime objects
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, date):
            return value.isoformat()

        # Handle sets (not JSON serializable)
        if isinstance(value, set):
            return sorted(list(value), key=str)

        # Handle bytes
        if isinstance(value, bytes):
            try:
                return value.decode('utf-8')
            except UnicodeDecodeError:
                return value.hex()

        # Handle nested dicts — create NEW dict, don't mutate
        if isinstance(value, dict):
            # This looks like it could cause mutation issues, but it creates
            # a completely new dict with coerced values
            new_dict = {}
            for k, v in value.items():
                str_key = str(k) if not isinstance(k, str) else k
                new_dict[str_key] = self._coerce_value(v)
            return new_dict

        # Handle nested lists — create NEW list
        if isinstance(value, (list, tuple)):
            return [self._coerce_value(item) for item in value]

        # Handle numeric edge cases
        if isinstance(value, float):
            if value != value:  # NaN check — looks weird but correct
                self._warnings.append("NaN value encountered, converting to null")
                return None
            if value == float('inf') or value == float('-inf'):
                self._warnings.append("Infinity value encountered, converting to null")
                return None

        # Strict type checking — reject unknown types
        if self._strict_types:
            if not isinstance(value, (str, int, float, bool)):
                raise TypeError(
                    f"Cannot serialize type {type(value).__name__} "
                    f"in strict mode"
                )

        return value

    def serialize_item(self, item):
        """Serialize a single item."""
        if isinstance(item, dict):
            return {k: self._coerce_value(v) for k, v in item.items()}
        return self._coerce_value(item)

    def serialize(self, items):
        """Serialize a list of items."""
        serialized = [self.serialize_item(item) for item in items]

        if self._format == 'json':
            return json.dumps(serialized, indent=2, default=str)
        elif self._format == 'csv':
            return self._to_csv(serialized)
        elif self._format == 'dict':
            return serialized
        else:
            raise ValueError(f"Unknown format: {self._format}")

    def _to_csv(self, items):
        """Convert items to CSV string."""
        if not items:
            return ""

        # Collect all headers
        headers = set()
        for item in items:
            if isinstance(item, dict):
                headers.update(item.keys())
        headers = sorted(headers)

        if not headers:
            return ""

        lines = [','.join(headers)]
        for item in items:
            if isinstance(item, dict):
                row = []
                for h in headers:
                    val = item.get(h, '')
                    str_val = str(val) if val is not None else ''
                    if ',' in str_val or '"' in str_val:
                        str_val = f'"{str_val}"'
                    row.append(str_val)
                lines.append(','.join(row))

        return '\n'.join(lines)

    def get_warnings(self):
        """Return serialization warnings."""
        return list(self._warnings)

    def clear_warnings(self):
        """Clear accumulated warnings."""
        self._warnings.clear()

    def __repr__(self):
        return (
            f"PipelineSerializer(format='{self._format}', "
            f"strict={self._strict_types})"
        )
