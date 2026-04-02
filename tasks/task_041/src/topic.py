"""
Topic for routing messages to subscribers.
Manages subscriptions and dispatches messages.
"""

import threading
from concurrent.futures import ThreadPoolExecutor


class Topic:
    """A named topic that routes messages to its subscribers.

    BUG: Messages are dispatched to subscribers using a thread pool
    for performance. This means subscriber.receive() is called from
    different threads, and the order of delivery is non-deterministic
    due to thread scheduling. Messages may arrive out of sequence order.
    """

    def __init__(self, name, max_workers=4):
        """Initialize a topic.

        Args:
            name: Topic name.
            max_workers: Number of worker threads for dispatch.
        """
        self.name = name
        self._subscribers = {}
        self._lock = threading.Lock()
        self._message_count = 0
        # BUG: thread pool dispatch causes ordering issues
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._dispatch_futures = []

    def subscribe(self, subscriber):
        """Add a subscriber to this topic."""
        with self._lock:
            self._subscribers[subscriber.id] = subscriber

    def unsubscribe(self, subscriber_id):
        """Remove a subscriber from this topic."""
        with self._lock:
            self._subscribers.pop(subscriber_id, None)

    def publish(self, message):
        """Publish a message to all subscribers.

        BUG: dispatches each subscriber delivery as a separate task
        in the thread pool. When multiple messages are published rapidly,
        message N might be delivered to subscriber X after message N+1
        because the thread for N was scheduled after the thread for N+1.
        """
        with self._lock:
            self._message_count += 1
            subscribers = list(self._subscribers.values())

        # BUG: each delivery is a separate thread task — no ordering guarantee
        for sub in subscribers:
            future = self._executor.submit(self._deliver, sub, message)
            self._dispatch_futures.append(future)

    def _deliver(self, subscriber, message):
        """Deliver a message to a single subscriber (runs in thread pool)."""
        subscriber.receive(message)

    def wait_for_delivery(self, timeout=5.0):
        """Wait for all pending deliveries to complete."""
        for future in self._dispatch_futures:
            future.result(timeout=timeout)
        self._dispatch_futures.clear()

    @property
    def subscriber_count(self):
        with self._lock:
            return len(self._subscribers)

    @property
    def message_count(self):
        return self._message_count

    def get_subscriber_ids(self):
        with self._lock:
            return list(self._subscribers.keys())

    def shutdown(self):
        """Shutdown the thread pool."""
        self._executor.shutdown(wait=True)

    def __repr__(self):
        return (
            f"Topic({self.name!r}, subscribers={self.subscriber_count}, "
            f"messages={self._message_count})"
        )
