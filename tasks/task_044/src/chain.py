"""Promise chain helper for managing ordered callback chains."""

from typing import Any, Callable, Optional


class ChainLink:
    """A single link in a promise chain."""

    def __init__(self, on_fulfilled: Optional[Callable] = None,
                 on_rejected: Optional[Callable] = None,
                 on_finally: Optional[Callable] = None):
        self.on_fulfilled = on_fulfilled
        self.on_rejected = on_rejected
        self.on_finally = on_finally


class PromiseChain:
    """Manages an ordered chain of callbacks with error propagation.

    When a value flows through the chain:
    - If the link has on_fulfilled, call it with the value.
    - If on_fulfilled raises, switch to error path.
    - Error path calls on_rejected if available, otherwise propagates.
    - on_finally is always called regardless of success/error.
    """

    def __init__(self):
        self._links: list[ChainLink] = []

    def add_link(self, link: ChainLink) -> None:
        """Append a link to the chain."""
        self._links.append(link)

    def execute(self, initial_value: Any = None, initial_error: Exception = None):
        """Execute the chain with an initial value or error.

        Should propagate values through on_fulfilled handlers and
        errors through on_rejected handlers, with proper switching
        between success and error paths.

        Returns:
            Tuple of (value, error) — one will be None.
        """
        raise NotImplementedError("PromiseChain.execute not yet implemented")
