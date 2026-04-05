"""
Type schema validator supporting primitive types, custom classes,
and generic container types with covariance checking.
"""

from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union
from dataclasses import dataclass, field


@dataclass
class TypeSchema:
    """Describes an expected type, possibly parameterized."""
    base_type: type
    type_params: List["TypeSchema"] = field(default_factory=list)
    nullable: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self):
        if self.type_params:
            params = ", ".join(repr(p) for p in self.type_params)
            return f"TypeSchema({self.base_type.__name__}[{params}])"
        return f"TypeSchema({self.base_type.__name__})"


@dataclass
class ValidationResult:
    """Result of a type validation check."""
    valid: bool
    errors: List[str] = field(default_factory=list)
    path: str = ""

    def add_error(self, message: str):
        self.valid = False
        prefix = f"at {self.path}: " if self.path else ""
        self.errors.append(f"{prefix}{message}")


class TypeRegistry:
    """Tracks type hierarchies for validation."""

    def __init__(self):
        self._types: Dict[str, type] = {}
        self._hierarchy: Dict[str, List[str]] = {}

    def register(self, cls: type, parent: Optional[type] = None):
        name = cls.__name__
        self._types[name] = cls
        if name not in self._hierarchy:
            self._hierarchy[name] = []
        if parent:
            parent_name = parent.__name__
            if parent_name not in self._hierarchy:
                self._hierarchy[parent_name] = []
            self._hierarchy[parent_name].append(name)

    def is_subtype(self, child: type, parent: type) -> bool:
        if child is parent:
            return True
        if issubclass(child, parent):
            return True
        child_name = child.__name__
        parent_name = parent.__name__
        return self._is_subtype_by_name(child_name, parent_name)

    def _is_subtype_by_name(self, child_name: str, parent_name: str) -> bool:
        if child_name == parent_name:
            return True
        for sub in self._hierarchy.get(parent_name, []):
            if self._is_subtype_by_name(child_name, sub):
                return True
        return False

    def get_registered(self) -> Dict[str, type]:
        return dict(self._types)


class TypeValidator:
    """Validates values against type schemas, supporting containers and covariance."""

    def __init__(self, registry: Optional[TypeRegistry] = None):
        self.registry = registry or TypeRegistry()

    def validate(self, value: Any, schema: TypeSchema,
                 path: str = "root") -> ValidationResult:
        result = ValidationResult(valid=True, path=path)

        if value is None:
            if schema.nullable:
                return result
            result.add_error(f"expected {schema.base_type.__name__}, got None")
            return result

        if schema.base_type is list:
            return self._validate_list(value, schema, path)
        elif schema.base_type is dict:
            return self._validate_dict(value, schema, path)
        elif schema.base_type is set:
            return self._validate_set(value, schema, path)
        elif schema.base_type is tuple:
            return self._validate_tuple(value, schema, path)
        else:
            return self._validate_simple(value, schema, path)

    def _validate_simple(self, value: Any, schema: TypeSchema,
                         path: str) -> ValidationResult:
        result = ValidationResult(valid=True, path=path)
        value_type = type(value)

        if value_type is schema.base_type:
            return result

        if self.registry.is_subtype(value_type, schema.base_type):
            return result

        result.add_error(
            f"expected {schema.base_type.__name__}, "
            f"got {value_type.__name__}")
        return result

    def _validate_list(self, value: Any, schema: TypeSchema,
                       path: str) -> ValidationResult:
        result = ValidationResult(valid=True, path=path)

        if not isinstance(value, list):
            result.add_error(f"expected list, got {type(value).__name__}")
            return result

        if not schema.type_params:
            return result

        elem_schema = schema.type_params[0]
        for i, item in enumerate(value):
            item_type = type(item)
            if item_type is not elem_schema.base_type:
                result.add_error(
                    f"element {i}: expected {elem_schema.base_type.__name__}, "
                    f"got {item_type.__name__}")

        return result

    def _validate_dict(self, value: Any, schema: TypeSchema,
                       path: str) -> ValidationResult:
        result = ValidationResult(valid=True, path=path)

        if not isinstance(value, dict):
            result.add_error(f"expected dict, got {type(value).__name__}")
            return result

        if len(schema.type_params) < 2:
            return result

        key_schema = schema.type_params[0]
        val_schema = schema.type_params[1]

        for k, v in value.items():
            key_type = type(k)
            if key_type is not key_schema.base_type:
                result.add_error(
                    f"key {k!r}: expected {key_schema.base_type.__name__}, "
                    f"got {key_type.__name__}")

            val_type = type(v)
            if val_type is not val_schema.base_type:
                result.add_error(
                    f"value for {k!r}: expected {val_schema.base_type.__name__}, "
                    f"got {val_type.__name__}")

        return result

    def _validate_set(self, value: Any, schema: TypeSchema,
                      path: str) -> ValidationResult:
        result = ValidationResult(valid=True, path=path)

        if not isinstance(value, set):
            result.add_error(f"expected set, got {type(value).__name__}")
            return result

        if not schema.type_params:
            return result

        elem_schema = schema.type_params[0]
        for item in value:
            item_type = type(item)
            if item_type is not elem_schema.base_type:
                result.add_error(
                    f"set element: expected {elem_schema.base_type.__name__}, "
                    f"got {item_type.__name__}")

        return result

    def _validate_tuple(self, value: Any, schema: TypeSchema,
                        path: str) -> ValidationResult:
        result = ValidationResult(valid=True, path=path)

        if not isinstance(value, tuple):
            result.add_error(f"expected tuple, got {type(value).__name__}")
            return result

        if not schema.type_params:
            return result

        if len(value) != len(schema.type_params):
            result.add_error(
                f"expected tuple of length {len(schema.type_params)}, "
                f"got length {len(value)}")
            return result

        for i, (item, param_schema) in enumerate(zip(value, schema.type_params)):
            sub = self.validate(item, param_schema, f"{path}[{i}]")
            if not sub.valid:
                result.valid = False
                result.errors.extend(sub.errors)

        return result

    def validate_schema_compatible(self, actual: TypeSchema,
                                   expected: TypeSchema) -> ValidationResult:
        result = ValidationResult(valid=True, path="schema")

        if actual.base_type is not expected.base_type:
            if not self.registry.is_subtype(actual.base_type, expected.base_type):
                result.add_error(
                    f"incompatible base: {actual.base_type.__name__} "
                    f"is not subtype of {expected.base_type.__name__}")
                return result

        if expected.type_params and actual.type_params:
            if len(actual.type_params) != len(expected.type_params):
                result.add_error("type parameter count mismatch")
                return result
            for i, (ap, ep) in enumerate(zip(actual.type_params,
                                             expected.type_params)):
                if ap.base_type is not ep.base_type:
                    result.add_error(
                        f"type param {i}: {ap.base_type.__name__} "
                        f"!= {ep.base_type.__name__}")

        return result


def make_list_schema(element_type: type, nullable: bool = False) -> TypeSchema:
    return TypeSchema(
        base_type=list,
        type_params=[TypeSchema(base_type=element_type)],
        nullable=nullable,
    )


def make_dict_schema(key_type: type, value_type: type,
                     nullable: bool = False) -> TypeSchema:
    return TypeSchema(
        base_type=dict,
        type_params=[
            TypeSchema(base_type=key_type),
            TypeSchema(base_type=value_type),
        ],
        nullable=nullable,
    )
