"""
Token Bucket Rate Limiter.

Implements a token bucket algorithm for rate limiting. Tokens are added
at a fixed rate and consumed when requests are made. The bucket has a
maximum capacity that should never be exceeded.
"""

import time


class TokenBucket:
    """Rate limiter using the token bucket algorithm.

    Tokens are added at a constant rate up to a maximum capacity.
    Each request consumes one or more tokens. If insufficient tokens
    are available, the request is denied.
    """

    def __init__(self, capacity, refill_rate):
        """Initialize the token bucket.

        Args:
            capacity: Maximum number of tokens the bucket can hold.
            refill_rate: Number of tokens added per second.

        Raises:
            ValueError: If capacity or refill_rate is not positive.
        """
        if capacity <= 0:
            raise ValueError("Capacity must be positive")
        if refill_rate <= 0:
            raise ValueError("Refill rate must be positive")

        self._capacity = capacity
        self._refill_rate = refill_rate
        self._tokens = float(capacity)
        self._last_refill = time.monotonic()

    @property
    def capacity(self):
        """Return the maximum token capacity."""
        return self._capacity

    @property
    def refill_rate(self):
        """Return the refill rate (tokens per second)."""
        return self._refill_rate

    @property
    def tokens(self):
        """Return the current number of available tokens."""
        return self._tokens

    def refill(self):
        """Refill tokens based on elapsed time since last refill.

        Adds tokens proportional to the time elapsed and the refill rate.
        """
        now = time.monotonic()
        elapsed = now - self._last_refill
        new_tokens = elapsed * self._refill_rate
        self._tokens += new_tokens
        self._last_refill = now

    def consume(self, count=1):
        """Attempt to consume tokens from the bucket.

        First refills based on elapsed time, then attempts to consume.

        Args:
            count: Number of tokens to consume. Defaults to 1.

        Returns:
            True if tokens were consumed, False if insufficient tokens.

        Raises:
            ValueError: If count is not positive.
        """
        if count <= 0:
            raise ValueError("Count must be positive")

        self.refill()

        if self._tokens >= count:
            self._tokens -= count
            return True
        return False

    def force_set_tokens(self, value):
        """Force-set the token count (for testing purposes).

        Args:
            value: Number of tokens to set.
        """
        self._tokens = float(value)
        self._last_refill = time.monotonic()

    def wait_for_tokens(self, count=1):
        """Calculate wait time needed for the given number of tokens.

        Args:
            count: Number of tokens needed.

        Returns:
            Wait time in seconds, or 0 if enough tokens are available.
        """
        self.refill()
        if self._tokens >= count:
            return 0.0
        deficit = count - self._tokens
        return deficit / self._refill_rate

    def __repr__(self):
        return (
            f"TokenBucket(capacity={self._capacity}, "
            f"rate={self._refill_rate}/s, "
            f"tokens={self._tokens:.1f})"
        )
