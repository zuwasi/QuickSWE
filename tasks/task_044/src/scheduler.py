"""Work scheduler for batching and scheduling work items."""

import threading
import time
from collections import deque
from typing import Any, Callable


class WorkItem:
    """A unit of work to be scheduled."""

    def __init__(self, fn: Callable, args: tuple = (), kwargs: dict = None,
                 priority: int = 0):
        self.fn = fn
        self.args = args
        self.kwargs = kwargs or {}
        self.priority = priority
        self.created_at = time.monotonic()
        self.result = None
        self.error = None
        self.completed = threading.Event()

    def execute(self):
        """Execute the work item and store the result."""
        try:
            self.result = self.fn(*self.args, **self.kwargs)
        except Exception as e:
            self.error = e
        finally:
            self.completed.set()


class WorkScheduler:
    """Schedules work items with priority ordering.

    Higher priority items are executed first. Items with the same
    priority are executed in FIFO order.
    """

    def __init__(self):
        self._queue: list[WorkItem] = []
        self._lock = threading.Lock()
        self._has_work = threading.Event()

    def schedule(self, item: WorkItem) -> None:
        """Add a work item to the schedule."""
        with self._lock:
            self._queue.append(item)
            self._queue.sort(key=lambda w: -w.priority)
            self._has_work.set()

    def next(self, timeout: float = None) -> WorkItem | None:
        """Get the next work item to execute.

        Args:
            timeout: Maximum seconds to wait for work.

        Returns:
            The next WorkItem, or None if timeout expired.
        """
        if not self._has_work.wait(timeout=timeout):
            return None
        with self._lock:
            if self._queue:
                item = self._queue.pop(0)
                if not self._queue:
                    self._has_work.clear()
                return item
        return None

    @property
    def pending_count(self) -> int:
        """Number of items waiting to be executed."""
        with self._lock:
            return len(self._queue)
