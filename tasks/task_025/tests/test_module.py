import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.type_validator import (
    TypeValidator, TypeRegistry, TypeSchema,
    make_list_schema, make_dict_schema,
)


class Animal:
    pass

class Dog(Animal):
    pass

class Cat(Animal):
    pass

class GoldenRetriever(Dog):
    pass


def make_registry():
    reg = TypeRegistry()
    reg.register(Animal)
    reg.register(Dog, parent=Animal)
    reg.register(Cat, parent=Animal)
    reg.register(GoldenRetriever, parent=Dog)
    return reg


class TestTypeValidatorPassToPass:
    """Tests that should pass both before and after the fix."""

    def test_simple_type_match(self):
        v = TypeValidator()
        result = v.validate(42, TypeSchema(base_type=int))
        assert result.valid

    def test_simple_type_mismatch(self):
        v = TypeValidator()
        result = v.validate("hello", TypeSchema(base_type=int))
        assert not result.valid

    def test_list_of_exact_type(self):
        v = TypeValidator()
        schema = make_list_schema(int)
        result = v.validate([1, 2, 3], schema)
        assert result.valid


@pytest.mark.fail_to_pass
class TestTypeValidatorFailToPass:
    """Tests that fail before the fix and pass after."""

    def test_list_of_subtype_is_valid(self):
        reg = make_registry()
        v = TypeValidator(registry=reg)
        schema = make_list_schema(Animal)
        dogs = [Dog(), Dog(), GoldenRetriever()]
        result = v.validate(dogs, schema)
        assert result.valid, f"Errors: {result.errors}"

    def test_dict_with_subtype_values(self):
        reg = make_registry()
        v = TypeValidator(registry=reg)
        schema = make_dict_schema(str, Animal)
        data = {"fido": Dog(), "whiskers": Cat()}
        result = v.validate(data, schema)
        assert result.valid, f"Errors: {result.errors}"

    def test_schema_compatibility_with_subtype_params(self):
        reg = make_registry()
        v = TypeValidator(registry=reg)
        actual = TypeSchema(base_type=list,
                           type_params=[TypeSchema(base_type=Dog)])
        expected = TypeSchema(base_type=list,
                             type_params=[TypeSchema(base_type=Animal)])
        result = v.validate_schema_compatible(actual, expected)
        assert result.valid, f"Errors: {result.errors}"
