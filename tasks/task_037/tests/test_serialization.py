"""Tests for the serialization layer."""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.schema import Schema, Field, FieldType, USER_SCHEMA
from src.serializer import Serializer, SerializationError
from src.validator import Validator, ValidationError
from src.store import Store, RecordNotFoundError


# ── pass-to-pass: these must always pass ─────────────────────────────────

class TestSchemaFieldDefinitions:
    """Schema and field definitions work correctly."""

    def test_schema_field_definitions(self):
        schema = Schema("test")
        schema.add_field(Field("name", FieldType.STRING, max_length=50))
        schema.add_field(Field("count", FieldType.INTEGER))

        assert schema.has_field("name")
        assert schema.has_field("count")
        assert not schema.has_field("other")

        name_field = schema.get_field("name")
        assert name_field.max_length == 50
        assert name_field.field_type == FieldType.STRING

        assert "name" in schema.field_names
        assert len(schema.get_fields()) == 2

        with pytest.raises(ValueError):
            schema.add_field(Field("name", FieldType.STRING))


class TestValidatorTypeChecks:
    """Validator catches type mismatches."""

    def test_validator_type_checks(self):
        validator = Validator(USER_SCHEMA)

        # Valid data
        valid_data = {
            "id": 1,
            "username": "alice",
            "full_name": "Alice Smith",
            "email": "alice@example.com",
        }
        assert validator.validate(valid_data) is True

        # Wrong type: string where int expected
        bad_data = {
            "id": "not_an_int",
            "username": "alice",
            "full_name": "Alice Smith",
            "email": "alice@example.com",
        }
        assert validator.validate(bad_data) is False
        assert len(validator.errors) > 0

        # Bool should not pass as int
        bool_data = {
            "id": True,
            "username": "alice",
            "full_name": "Alice Smith",
            "email": "alice@example.com",
        }
        assert validator.validate(bool_data) is False


class TestStoreBasicCrud:
    """Basic CRUD operations on the store."""

    def test_store_basic_crud(self):
        store = Store(USER_SCHEMA)

        # Create
        rid = store.save({
            "id": 1,
            "username": "bob",
            "full_name": "Bob Jones",
            "email": "bob@test.com",
        })
        assert rid == 1
        assert store.count == 1

        # Read
        record = store.get(1)
        assert record["username"] == "bob"

        # Update
        store.update(1, {"email": "bob_new@test.com"})
        updated = store.get(1)
        assert updated["email"] == "bob_new@test.com"

        # Delete
        store.delete(1)
        assert store.count == 0
        with pytest.raises(RecordNotFoundError):
            store.get(1)


# ── fail-to-pass: these FAIL with the bug, PASS after fix ────────────────

class TestSerializerMaxLength:
    """Serializer must enforce max_length, not silently truncate."""

    @pytest.mark.fail_to_pass
    def test_serializer_enforces_max_length(self):
        """Serializer.serialize() should raise when a string exceeds max_length."""
        serializer = Serializer(USER_SCHEMA)

        long_name = "A" * 80  # max_length for full_name is 50

        data = {
            "id": 1,
            "username": "testuser",
            "full_name": long_name,
            "email": "test@example.com",
        }

        # BUG: serialize() silently truncates to 50 chars instead of raising
        with pytest.raises(SerializationError) as exc_info:
            serializer.serialize(data)

        assert "max_length" in str(exc_info.value).lower() or \
               "50" in str(exc_info.value)


class TestStoreRejectsOversized:
    """Store should reject records with oversized fields."""

    @pytest.mark.fail_to_pass
    def test_store_rejects_oversized_fields(self):
        """Store.save() must not silently truncate data."""
        store = Store(USER_SCHEMA)

        long_bio = "X" * 300  # max_length for bio is 200

        data = {
            "id": 1,
            "username": "testuser",
            "full_name": "Test User",
            "email": "test@example.com",
            "bio": long_bio,
        }

        # BUG: save() calls serialize() which truncates without error
        with pytest.raises((SerializationError, ValueError)):
            store.save(data)


class TestRoundtripPreservation:
    """Data must survive a save/load roundtrip without loss."""

    @pytest.mark.fail_to_pass
    def test_roundtrip_preserves_full_data(self):
        """Saving and loading a record must preserve all data exactly."""
        store = Store(USER_SCHEMA)

        # This name is exactly at max_length (50 chars)
        exact_name = "A" * 50
        # This email is under max_length
        email = "longuser@example.com"

        data = {
            "id": 1,
            "username": "shortuser",
            "full_name": exact_name,
            "email": email,
        }
        store.save(data)
        retrieved = store.get(1)

        assert retrieved["full_name"] == exact_name, (
            f"Name was {len(retrieved['full_name'])} chars, "
            f"expected {len(exact_name)}"
        )

        # Now try with a name that's 51 chars — should fail, not truncate
        data2 = {
            "id": 2,
            "username": "another",
            "full_name": "B" * 51,
            "email": "b@test.com",
        }
        with pytest.raises((SerializationError, ValueError)):
            store.save(data2)
