"""Retry decorator with exponential backoff."""

import functools
import time
from typing import Any, Callable, Optional, Sequence, Type, Union


class MaxRetriesExceededError(Exception):
    """Raised when all retry attempts have been exhausted."""

    def __init__(self, func_name: str, attempts: int,
                 last_exception: Exception):
        self.func_name = func_name
        self.attempts = attempts
        self.last_exception = last_exception
        super().__init__(
            f"{func_name} failed after {attempts} attempts: {last_exception}"
        )


def retry(
    max_retries: int = 3,
    backoff_base: float = 0.1,
    backoff_factor: float = 2.0,
    retryable_exceptions: Union[
        Type[Exception], Sequence[Type[Exception]]
    ] = Exception,
    on_retry: Optional[Callable] = None,
) -> Callable:
    """Decorator that retries a function on failure.

    Args:
        max_retries: Maximum number of retry attempts.
        backoff_base: Initial delay in seconds.
        backoff_factor: Multiplier applied to delay after each attempt.
        retryable_exceptions: Exception types that trigger a retry.
        on_retry: Optional callback(attempt, exception, delay) called
                  before each retry sleep.
    """
    if isinstance(retryable_exceptions, type):
        retryable_exceptions = (retryable_exceptions,)
    else:
        retryable_exceptions = tuple(retryable_exceptions)

    def decorator(func: Callable) -> Callable:
        attempts_used = 0

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            nonlocal attempts_used
            last_exc: Optional[Exception] = None

            while attempts_used <= max_retries:
                try:
                    result = func(*args, **kwargs)
                    return result
                except retryable_exceptions as exc:
                    last_exc = exc
                    attempts_used += 1

                    if attempts_used > max_retries:
                        break

                    delay = backoff_base * (backoff_factor ** (attempts_used - 1))

                    if on_retry is not None:
                        on_retry(attempts_used, exc, delay)

                    time.sleep(delay)

            raise MaxRetriesExceededError(
                func.__name__, attempts_used, last_exc
            )

        wrapper.max_retries = max_retries
        wrapper.backoff_base = backoff_base
        wrapper.backoff_factor = backoff_factor
        return wrapper

    return decorator


def retry_async(
    max_retries: int = 3,
    backoff_base: float = 0.1,
    backoff_factor: float = 2.0,
    retryable_exceptions: Union[
        Type[Exception], Sequence[Type[Exception]]
    ] = Exception,
) -> Callable:
    """Async version of the retry decorator."""
    import asyncio

    if isinstance(retryable_exceptions, type):
        retryable_exceptions = (retryable_exceptions,)
    else:
        retryable_exceptions = tuple(retryable_exceptions)

    def decorator(func: Callable) -> Callable:
        attempts_used = 0

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            nonlocal attempts_used
            last_exc = None

            while attempts_used <= max_retries:
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as exc:
                    last_exc = exc
                    attempts_used += 1
                    if attempts_used > max_retries:
                        break
                    delay = backoff_base * (backoff_factor ** (attempts_used - 1))
                    await asyncio.sleep(delay)

            raise MaxRetriesExceededError(
                func.__name__, attempts_used, last_exc
            )

        wrapper.max_retries = max_retries
        return wrapper

    return decorator


class RetryBudget:
    """A token-bucket style retry budget shared across multiple callers."""

    def __init__(self, max_retries_per_window: int, window_seconds: float):
        self._max = max_retries_per_window
        self._window = window_seconds
        self._timestamps: list = []

    def can_retry(self) -> bool:
        now = time.monotonic()
        self._timestamps = [
            t for t in self._timestamps if now - t < self._window
        ]
        return len(self._timestamps) < self._max

    def record_retry(self) -> None:
        self._timestamps.append(time.monotonic())

    @property
    def remaining(self) -> int:
        now = time.monotonic()
        recent = sum(1 for t in self._timestamps if now - t < self._window)
        return max(0, self._max - recent)
