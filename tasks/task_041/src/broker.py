"""
Message broker that manages topics and routes messages.
Central hub for the pub/sub system.
"""

import threading
from .topic import Topic
from .subscriber import Subscriber


class MessageBroker:
    """Central message broker for pub/sub.

    Manages topics, subscriptions, and message routing.
    """

    def __init__(self, default_workers=4):
        """Initialize the broker.

        Args:
            default_workers: Default thread pool size for topic dispatch.
        """
        self._topics = {}
        self._lock = threading.Lock()
        self._default_workers = default_workers
        self._total_routed = 0

    def create_topic(self, name, max_workers=None):
        """Create a new topic."""
        workers = max_workers if max_workers is not None else self._default_workers
        with self._lock:
            if name in self._topics:
                return self._topics[name]
            topic = Topic(name, max_workers=workers)
            self._topics[name] = topic
            return topic

    def get_topic(self, name):
        """Get an existing topic."""
        with self._lock:
            return self._topics.get(name)

    def subscribe(self, topic_name, subscriber):
        """Subscribe to a topic. Creates the topic if it doesn't exist."""
        topic = self.create_topic(topic_name)
        topic.subscribe(subscriber)

    def unsubscribe(self, topic_name, subscriber_id):
        """Unsubscribe from a topic."""
        with self._lock:
            topic = self._topics.get(topic_name)
        if topic:
            topic.unsubscribe(subscriber_id)

    def publish(self, topic_name, message):
        """Route a message to the appropriate topic."""
        with self._lock:
            topic = self._topics.get(topic_name)
            self._total_routed += 1

        if topic is None:
            return False

        topic.publish(message)
        return True

    def wait_all(self, timeout=5.0):
        """Wait for all pending message deliveries across all topics."""
        with self._lock:
            topics = list(self._topics.values())

        for topic in topics:
            topic.wait_for_delivery(timeout=timeout)

    def shutdown(self):
        """Shutdown all topics and their thread pools."""
        with self._lock:
            topics = list(self._topics.values())
        for topic in topics:
            topic.shutdown()

    @property
    def topic_count(self):
        with self._lock:
            return len(self._topics)

    @property
    def total_routed(self):
        return self._total_routed

    def topic_names(self):
        with self._lock:
            return list(self._topics.keys())

    def __repr__(self):
        return (
            f"MessageBroker(topics={self.topic_count}, "
            f"routed={self._total_routed})"
        )
