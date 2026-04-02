"""
Data store module for persisting records.
Uses the serializer to prepare data for storage.
"""

from .serializer import Serializer, SerializationError


class RecordNotFoundError(Exception):
    """Raised when a record is not found."""
    pass


class Store:
    """In-memory store that serializes records according to a schema."""

    def __init__(self, schema):
        self.schema = schema
        # BUG: uses Serializer.serialize() which does NOT enforce max_length
        # Should use validate_and_serialize() or add max_length check to serialize()
        self._serializer = Serializer(schema)
        self._records = {}
        self._next_id = 1

    def save(self, data):
        """Save a record to the store.

        Serializes the data and stores it. Returns the record ID.
        """
        # BUG: calls serialize() instead of validate_and_serialize()
        # This means max_length is silently truncated, not rejected
        serialized = self._serializer.serialize(data)

        record_id = data.get("id", self._next_id)
        self._records[record_id] = serialized
        if record_id >= self._next_id:
            self._next_id = record_id + 1

        return record_id

    def get(self, record_id):
        """Retrieve a record by ID."""
        if record_id not in self._records:
            raise RecordNotFoundError(f"Record {record_id} not found")
        return self._serializer.deserialize(self._records[record_id])

    def update(self, record_id, data):
        """Update an existing record."""
        if record_id not in self._records:
            raise RecordNotFoundError(f"Record {record_id} not found")

        existing = self._records[record_id].copy()
        serialized = self._serializer.serialize({**existing, **data})
        self._records[record_id] = serialized
        return record_id

    def delete(self, record_id):
        """Delete a record."""
        if record_id not in self._records:
            raise RecordNotFoundError(f"Record {record_id} not found")
        del self._records[record_id]

    def list_all(self):
        """List all records."""
        return {
            rid: self._serializer.deserialize(data)
            for rid, data in self._records.items()
        }

    @property
    def count(self):
        return len(self._records)

    def find(self, **criteria):
        """Find records matching criteria."""
        results = []
        for rid, data in self._records.items():
            record = self._serializer.deserialize(data)
            match = all(record.get(k) == v for k, v in criteria.items())
            if match:
                results.append((rid, record))
        return results
