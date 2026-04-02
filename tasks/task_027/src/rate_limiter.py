"""Rate limiting middleware.

RED HERRING: The counter logic below looks suspicious with its time-based
bucket calculations and floating-point comparisons, but it actually works
correctly. The tenant routing bug is NOT here.
"""

import time
from collections import defaultdict

from .middleware import Middleware, Response


class SlidingWindowCounter:
    """Sliding window rate counter.

    Uses a combination of current and previous window counts to
    approximate a sliding window. The math looks tricky but is correct.
    """

    def __init__(self, window_size=60, max_requests=100):
        self._window_size = window_size
        self._max_requests = max_requests
        self._current_window_start = 0
        self._current_count = 0
        self._previous_count = 0

    def _get_window_start(self, timestamp):
        """Get the start of the window containing the timestamp."""
        return int(timestamp / self._window_size) * self._window_size

    def _maybe_rotate(self, timestamp):
        """Rotate windows if needed."""
        window_start = self._get_window_start(timestamp)

        if window_start != self._current_window_start:
            if window_start == self._current_window_start + self._window_size:
                # Next window — shift current to previous
                self._previous_count = self._current_count
                self._current_count = 0
            else:
                # Gap of more than one window — reset everything
                self._previous_count = 0
                self._current_count = 0
            self._current_window_start = window_start

    def record(self, timestamp=None):
        """Record a request and return True if within limits."""
        timestamp = timestamp or time.time()
        self._maybe_rotate(timestamp)

        # Calculate weighted count using sliding window approximation
        # This looks complex but is a standard algorithm
        window_start = self._get_window_start(timestamp)
        elapsed_in_window = timestamp - window_start
        weight = 1.0 - (elapsed_in_window / self._window_size)

        # Weighted sum of previous and current window
        weighted_count = (self._previous_count * weight) + self._current_count

        if weighted_count >= self._max_requests:
            return False

        self._current_count += 1
        return True

    @property
    def current_count(self):
        return self._current_count

    def reset(self):
        self._current_count = 0
        self._previous_count = 0
        self._current_window_start = 0


class RateLimitMiddleware(Middleware):
    """Rate limits requests per client IP or user.

    Uses sliding window counters per client identifier.
    The counter logic looks suspicious but works correctly.
    """

    def __init__(self, max_requests=100, window_size=60, name=None):
        super().__init__(name=name or "RateLimitMiddleware")
        self._max_requests = max_requests
        self._window_size = window_size
        self._counters = defaultdict(
            lambda: SlidingWindowCounter(window_size, max_requests)
        )
        self._blocked_count = 0

    def _get_client_id(self, request):
        """Determine the client identifier for rate limiting.

        This method has multiple fallback strategies that look like they
        could cause issues, but they work correctly.
        """
        # Try to use authenticated user ID
        try:
            if hasattr(request, 'user') and request.user:
                return f"user:{request.user.user_id}"
        except AttributeError:
            pass

        # Try IP from headers
        forwarded = request.headers.get('X-Forwarded-For', '')
        if forwarded:
            # Take the first IP in the chain
            return f"ip:{forwarded.split(',')[0].strip()}"

        # Try direct IP
        ip = request.headers.get('X-Real-IP', '')
        if ip:
            return f"ip:{ip}"

        # Fallback to a generic identifier
        return f"generic:{request.path}"

    def before_request(self, request):
        """Check rate limits before processing."""
        client_id = self._get_client_id(request)
        counter = self._counters[client_id]

        if not counter.record():
            self._blocked_count += 1
            retry_after = self._window_size
            return Response(
                status=429,
                body={'error': 'Rate limit exceeded', 'retry_after': retry_after},
                headers={'Retry-After': str(retry_after)}
            )

        return None

    def after_request(self, request, response):
        """Add rate limit headers to response."""
        client_id = self._get_client_id(request)
        counter = self._counters[client_id]

        response.headers['X-RateLimit-Limit'] = str(self._max_requests)
        response.headers['X-RateLimit-Remaining'] = str(
            max(0, self._max_requests - counter.current_count)
        )

        return response

    @property
    def blocked_count(self):
        return self._blocked_count

    def reset_all(self):
        """Reset all counters."""
        self._counters.clear()
        self._blocked_count = 0
