"""Promise implementation for async task handling."""

import threading
from enum import Enum
from typing import Any, Callable, Optional


class PromiseState(Enum):
    PENDING = "pending"
    FULFILLED = "fulfilled"
    REJECTED = "rejected"


class Promise:
    """A JavaScript-style Promise for Python.

    Usage:
        def executor(resolve, reject):
            resolve(42)

        p = Promise(executor)
        p.then(lambda v: print(v))  # prints 42
    """

    def __init__(self, executor_fn: Callable):
        """Create a new Promise.

        Args:
            executor_fn: A function that takes (resolve, reject) callbacks.
                         Called immediately upon construction.
        """
        self._state = PromiseState.PENDING
        self._value = None
        self._reason = None
        self._lock = threading.Lock()
        self._event = threading.Event()
        self._then_callbacks: list = []
        self._catch_callbacks: list = []
        self._finally_callbacks: list = []
        # TODO: call executor_fn with resolve/reject
        raise NotImplementedError("Promise.__init__ not yet implemented")

    def then(self, on_fulfilled: Optional[Callable] = None,
             on_rejected: Optional[Callable] = None) -> "Promise":
        """Chain a fulfillment and/or rejection handler.

        Returns a new Promise that resolves with the return value of the handler.
        """
        raise NotImplementedError("Promise.then not yet implemented")

    def catch(self, on_rejected: Callable) -> "Promise":
        """Chain a rejection handler. Shorthand for .then(None, on_rejected)."""
        raise NotImplementedError("Promise.catch not yet implemented")

    def finally_(self, on_settled: Callable) -> "Promise":
        """Chain a handler called on settlement (resolve or reject).

        The handler receives no arguments. The returned Promise preserves
        the original result/rejection.
        """
        raise NotImplementedError("Promise.finally_ not yet implemented")

    def result(self, timeout: Optional[float] = None) -> Any:
        """Block until settled and return the value or raise the rejection reason.

        Args:
            timeout: Maximum seconds to wait. None = wait forever.

        Raises:
            TimeoutError: If timeout expires before settlement.
            Exception: The rejection reason if the promise was rejected.
        """
        raise NotImplementedError("Promise.result not yet implemented")

    @classmethod
    def resolve(cls, value: Any) -> "Promise":
        """Create an immediately resolved Promise."""
        raise NotImplementedError("Promise.resolve not yet implemented")

    @classmethod
    def reject(cls, reason: Exception) -> "Promise":
        """Create an immediately rejected Promise."""
        raise NotImplementedError("Promise.reject not yet implemented")

    @classmethod
    def all(cls, promises: list["Promise"]) -> "Promise":
        """Return a Promise that resolves when all input promises resolve.

        Resolves with a list of values in the same order.
        Rejects immediately if any input promise rejects.
        """
        raise NotImplementedError("Promise.all not yet implemented")

    @classmethod
    def race(cls, promises: list["Promise"]) -> "Promise":
        """Return a Promise that settles with the first settled input promise."""
        raise NotImplementedError("Promise.race not yet implemented")
