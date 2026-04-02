"""Task executor with thread pool that returns Promises."""

import threading
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Any, Callable


class TaskExecutor:
    """Executes tasks in a thread pool.

    Currently returns raw concurrent.futures.Future objects.
    Should be updated to return Promise objects instead.
    """

    def __init__(self, max_workers: int = 4):
        self._pool = ThreadPoolExecutor(max_workers=max_workers)
        self._active_count = 0
        self._lock = threading.Lock()

    def submit(self, fn: Callable, *args: Any, **kwargs: Any) -> Future:
        """Submit a callable for execution.

        Currently returns a concurrent.futures.Future. Should return a Promise.

        Args:
            fn: The callable to execute.
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            A Future (should be changed to Promise).
        """
        with self._lock:
            self._active_count += 1

        def wrapper():
            try:
                return fn(*args, **kwargs)
            finally:
                with self._lock:
                    self._active_count -= 1

        return self._pool.submit(wrapper)

    @property
    def active_tasks(self) -> int:
        """Return the number of currently executing tasks."""
        with self._lock:
            return self._active_count

    def shutdown(self, wait: bool = True):
        """Shut down the executor."""
        self._pool.shutdown(wait=wait)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.shutdown()
