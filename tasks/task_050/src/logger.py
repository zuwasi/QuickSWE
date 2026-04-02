"""Callback-based logger — needs to be made async-compatible."""

import time
from dataclasses import dataclass, field


@dataclass
class LogEntry:
    """A single log entry."""
    event: str
    message: str
    timestamp: float = field(default_factory=time.monotonic)
    level: str = "INFO"


class Logger:
    """Callback-based logger that records events.

    Currently works with callbacks. Should be usable from async context
    after refactoring (can remain sync internally).
    """

    def __init__(self):
        self._entries: list[LogEntry] = []
        self._callbacks: dict[str, list] = {}

    def on(self, event: str, callback) -> None:
        """Register a callback for an event type."""
        self._callbacks.setdefault(event, []).append(callback)

    def log(self, event: str, message: str, level: str = "INFO") -> None:
        """Log an event."""
        entry = LogEntry(event=event, message=message, level=level)
        self._entries.append(entry)
        for cb in self._callbacks.get(event, []):
            cb(entry)

    def get_entries(self, event: str = None) -> list[LogEntry]:
        """Get log entries, optionally filtered by event."""
        if event:
            return [e for e in self._entries if e.event == event]
        return list(self._entries)

    def clear(self) -> None:
        """Clear all log entries."""
        self._entries.clear()

    @property
    def entry_count(self) -> int:
        return len(self._entries)
