"""
Subscriber for receiving messages from topics.
Maintains a message queue and tracks received messages.
"""

import threading
from collections import deque


class Subscriber:
    """A subscriber that receives messages from topics.

    Messages are placed in a thread-safe queue for consumption.
    """

    _id_counter = 0
    _id_lock = threading.Lock()

    def __init__(self, name=None, max_queue_size=10000):
        """Initialize a subscriber.

        Args:
            name: Human-readable name.
            max_queue_size: Maximum queue size before dropping.
        """
        with Subscriber._id_lock:
            Subscriber._id_counter += 1
            self.id = Subscriber._id_counter

        self.name = name or f"subscriber_{self.id}"
        self.max_queue_size = max_queue_size
        self._queue = deque()
        self._lock = threading.Lock()
        self._received_count = 0
        self._dropped_count = 0
        self._last_sequence = -1

    def receive(self, message):
        """Receive a message and add it to the queue.

        This is called by the Topic/Broker to deliver messages.
        Thread-safe.
        """
        with self._lock:
            if len(self._queue) >= self.max_queue_size:
                self._dropped_count += 1
                return False
            self._queue.append(message)
            self._received_count += 1
            message.mark_delivered(self.id)
            return True

    def poll(self):
        """Get the next message from the queue.

        Returns None if queue is empty.
        """
        with self._lock:
            if self._queue:
                msg = self._queue.popleft()
                self._last_sequence = msg.sequence
                return msg
            return None

    def poll_all(self):
        """Get all messages from the queue."""
        with self._lock:
            messages = list(self._queue)
            self._queue.clear()
            if messages:
                self._last_sequence = messages[-1].sequence
            return messages

    def drain(self):
        """Drain queue and return messages in order received."""
        return self.poll_all()

    @property
    def queue_size(self):
        with self._lock:
            return len(self._queue)

    @property
    def received_count(self):
        return self._received_count

    @property
    def dropped_count(self):
        return self._dropped_count

    @property
    def last_sequence(self):
        return self._last_sequence

    def is_ordered(self):
        """Check if received messages are in sequence order.

        Must be called BEFORE draining the queue.
        """
        with self._lock:
            messages = list(self._queue)

        for i in range(1, len(messages)):
            if messages[i].sequence < messages[i - 1].sequence:
                return False
        return True

    def get_sequence_gaps(self):
        """Find gaps or reorderings in the received sequence."""
        with self._lock:
            messages = list(self._queue)

        issues = []
        for i in range(1, len(messages)):
            if messages[i].sequence <= messages[i - 1].sequence:
                issues.append({
                    "index": i,
                    "prev_seq": messages[i - 1].sequence,
                    "curr_seq": messages[i].sequence,
                })
        return issues

    def __repr__(self):
        return (
            f"Subscriber({self.name!r}, queue={self.queue_size}, "
            f"received={self._received_count})"
        )

    @classmethod
    def reset_ids(cls):
        with cls._id_lock:
            cls._id_counter = 0
