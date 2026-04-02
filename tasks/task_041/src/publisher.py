"""
Publisher for sending messages to topics.
Assigns sequence numbers and routes to the correct topic.
"""

import threading
from .message import Message


class Publisher:
    """Publishes messages to topics through the broker.

    Maintains its own per-topic sequence numbers for ordering.
    """

    def __init__(self, broker, name=None):
        """Initialize a publisher.

        Args:
            broker: MessageBroker instance.
            name: Human-readable name.
        """
        self._broker = broker
        self.name = name or "publisher"
        self._sequence_lock = threading.Lock()
        self._sequences = {}
        self._total_published = 0

    def publish(self, topic_name, payload):
        """Publish a message to a topic.

        Assigns a per-topic sequence number and sends through the broker.
        """
        with self._sequence_lock:
            seq = self._sequences.get(topic_name, 0) + 1
            self._sequences[topic_name] = seq
            self._total_published += 1

        message = Message(topic_name, payload, sequence=seq)
        self._broker.publish(topic_name, message)
        return message

    def publish_batch(self, topic_name, payloads):
        """Publish multiple messages to a topic."""
        messages = []
        for payload in payloads:
            msg = self.publish(topic_name, payload)
            messages.append(msg)
        return messages

    @property
    def total_published(self):
        return self._total_published

    def get_sequence(self, topic_name):
        """Get the current sequence number for a topic."""
        return self._sequences.get(topic_name, 0)

    def __repr__(self):
        return f"Publisher({self.name!r}, published={self._total_published})"
