"""Data sources that emit observable events."""

import time
import random
from .observable import Observable


class DataSource(Observable):
    """A data source that periodically produces data and notifies observers."""

    def __init__(self, source_id: str, data_type: str = "numeric"):
        super().__init__()
        self.source_id = source_id
        self.data_type = data_type
        self._last_value = None
        self._emit_count = 0

    def emit(self, value=None):
        """Emit a data point and notify observers.

        Args:
            value: The data value to emit. If None, a random value is generated.
        """
        if value is None:
            value = random.random() * 100

        self._last_value = value
        self._emit_count += 1

        self.notify("data", {
            "source_id": self.source_id,
            "value": value,
            "timestamp": time.time(),
            "sequence": self._emit_count,
        })

    def emit_status(self, status: str):
        """Emit a status event."""
        self.notify("status", {
            "source_id": self.source_id,
            "status": status,
        })

    @property
    def last_value(self):
        return self._last_value

    @property
    def emit_count(self):
        return self._emit_count

    def __repr__(self):
        return f"DataSource({self.source_id!r})"
