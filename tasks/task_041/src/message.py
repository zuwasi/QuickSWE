"""
Message definition for the pub/sub system.
Messages carry a payload, sequence number, and metadata.
"""

import time
import threading


class Message:
    """A message in the pub/sub system.

    Each message has a globally unique sequence number assigned
    by the publisher, a topic, a payload, and a timestamp.
    """

    _global_seq_lock = threading.Lock()
    _global_seq = 0

    def __init__(self, topic, payload, sequence=None):
        """Initialize a message.

        Args:
            topic: Topic name this message belongs to.
            payload: Message payload (any serializable data).
            sequence: Sequence number. Auto-assigned if None.
        """
        self.topic = topic
        self.payload = payload
        self.timestamp = time.monotonic()
        self.created_at = time.time()

        if sequence is not None:
            self.sequence = sequence
        else:
            with Message._global_seq_lock:
                Message._global_seq += 1
                self.sequence = Message._global_seq

        self._delivered_to = set()

    def mark_delivered(self, subscriber_id):
        """Mark this message as delivered to a subscriber."""
        self._delivered_to.add(subscriber_id)

    @property
    def delivery_count(self):
        return len(self._delivered_to)

    def is_delivered_to(self, subscriber_id):
        return subscriber_id in self._delivered_to

    def __repr__(self):
        return (
            f"Message(topic={self.topic!r}, seq={self.sequence}, "
            f"payload={self.payload!r})"
        )

    def __eq__(self, other):
        if not isinstance(other, Message):
            return NotImplemented
        return self.sequence == other.sequence and self.topic == other.topic

    def __hash__(self):
        return hash((self.topic, self.sequence))

    @classmethod
    def reset_sequence(cls):
        """Reset global sequence counter (for testing)."""
        with cls._global_seq_lock:
            cls._global_seq = 0
