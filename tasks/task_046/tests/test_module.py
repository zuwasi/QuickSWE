import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.type_inference import (
    TypeVar, ConcreteType, FunctionType, ConstructedType,
    unify, free_type_vars, resolve_type, type_to_string,
    INT, BOOL, STRING, fresh_type_var, list_type, option_type,
    TypeError as TypError,
)


class TestBasicUnification:
    """Tests that should pass both before and after the fix."""

    @pytest.mark.pass_to_pass
    def test_unify_concrete_same(self):
        unify(INT, INT)  # should not raise

    @pytest.mark.pass_to_pass
    def test_unify_concrete_different(self):
        with pytest.raises(TypError):
            unify(INT, BOOL)

    @pytest.mark.pass_to_pass
    def test_unify_type_var_with_concrete(self):
        t = fresh_type_var()
        unify(t, INT)
        assert resolve_type(t) == INT


class TestOccursCheck:
    """Tests that should fail before the fix and pass after."""

    @pytest.mark.fail_to_pass
    def test_occurs_check_direct(self):
        """Unifying t with List[t] should raise TypeError (not silently create infinite type)."""
        t = fresh_type_var()
        with pytest.raises(TypError, match="[Oo]ccur|[Ii]nfinite|[Rr]ecursive"):
            unify(t, list_type(t))

    @pytest.mark.fail_to_pass
    def test_occurs_check_function(self):
        """Unifying t with (t -> Int) should raise TypeError."""
        t = fresh_type_var()
        with pytest.raises(TypError, match="[Oo]ccur|[Ii]nfinite|[Rr]ecursive"):
            unify(t, FunctionType(t, INT))

    @pytest.mark.fail_to_pass
    def test_occurs_check_nested(self):
        """Unifying t with List[Option[t]] should raise TypeError."""
        t = fresh_type_var()
        with pytest.raises(TypError, match="[Oo]ccur|[Ii]nfinite|[Rr]ecursive"):
            unify(t, list_type(option_type(t)))
