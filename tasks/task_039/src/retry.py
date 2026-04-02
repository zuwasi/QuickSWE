"""
Retry policy for database operations.
Provides configurable retry logic with backoff.
"""

import time


class RetryExhaustedError(Exception):
    """Raised when all retries are exhausted."""
    pass


class RetryPolicy:
    """Configurable retry policy with optional backoff.

    Wraps a callable and retries it on specified exception types.
    """

    def __init__(self, max_retries=3, retry_on=None, backoff=0.0,
                 backoff_multiplier=1.0):
        """Initialize retry policy.

        Args:
            max_retries: Maximum number of retry attempts.
            retry_on: Tuple of exception types to retry on.
            backoff: Initial backoff delay in seconds.
            backoff_multiplier: Multiplier for exponential backoff.
        """
        self.max_retries = max_retries
        self.retry_on = retry_on or (Exception,)
        self.backoff = backoff
        self.backoff_multiplier = backoff_multiplier
        self._attempt_count = 0
        self._last_error = None

    def execute(self, func, *args, **kwargs):
        """Execute func with retries.

        Returns the result on success, raises RetryExhaustedError on failure.
        """
        self._attempt_count = 0
        delay = self.backoff

        for attempt in range(self.max_retries + 1):
            self._attempt_count = attempt + 1
            try:
                return func(*args, **kwargs)
            except self.retry_on as e:
                self._last_error = e
                if attempt < self.max_retries:
                    if delay > 0:
                        time.sleep(delay)
                    delay *= self.backoff_multiplier
                else:
                    raise RetryExhaustedError(
                        f"Failed after {self.max_retries + 1} attempts: {e}"
                    ) from e

    @property
    def attempts(self):
        return self._attempt_count

    @property
    def last_error(self):
        return self._last_error

    def reset(self):
        """Reset attempt counter."""
        self._attempt_count = 0
        self._last_error = None

    def __repr__(self):
        return (
            f"RetryPolicy(max_retries={self.max_retries}, "
            f"attempts={self._attempt_count})"
        )


class NoRetry(RetryPolicy):
    """A policy that never retries. Useful for testing."""

    def __init__(self):
        super().__init__(max_retries=0)
