"""Tests for pub/sub message ordering."""

import sys
import os
import time
import threading
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.message import Message
from src.subscriber import Subscriber
from src.topic import Topic
from src.publisher import Publisher
from src.broker import MessageBroker


@pytest.fixture(autouse=True)
def reset_counters():
    """Reset global counters before each test."""
    Message.reset_sequence()
    Subscriber.reset_ids()
    yield


# ── pass-to-pass: these must always pass ─────────────────────────────────

class TestSingleMessageDelivery:
    """Single message delivery works fine."""

    def test_single_message_delivery(self):
        broker = MessageBroker(default_workers=1)
        broker.create_topic("test", max_workers=1)
        sub = Subscriber(name="s1")
        broker.subscribe("test", sub)

        pub = Publisher(broker, name="p1")
        pub.publish("test", "hello")

        broker.wait_all()
        broker.shutdown()

        assert sub.queue_size == 1
        msg = sub.poll()
        assert msg.payload == "hello"
        assert msg.sequence == 1


class TestSubscriberQueueOperations:
    """Subscriber queue operations are correct."""

    def test_subscriber_queue_operations(self):
        sub = Subscriber(name="test_sub")
        assert sub.queue_size == 0

        msg1 = Message("t", "a", sequence=1)
        msg2 = Message("t", "b", sequence=2)
        msg3 = Message("t", "c", sequence=3)

        sub.receive(msg1)
        sub.receive(msg2)
        sub.receive(msg3)

        assert sub.queue_size == 3
        assert sub.received_count == 3

        polled = sub.poll()
        assert polled.payload == "a"
        assert sub.queue_size == 2

        all_remaining = sub.poll_all()
        assert len(all_remaining) == 2
        assert sub.queue_size == 0


class TestTopicSubscribeUnsubscribe:
    """Topic subscription management."""

    def test_topic_subscribe_unsubscribe(self):
        topic = Topic("test", max_workers=1)
        s1 = Subscriber(name="s1")
        s2 = Subscriber(name="s2")

        topic.subscribe(s1)
        topic.subscribe(s2)
        assert topic.subscriber_count == 2

        topic.unsubscribe(s1.id)
        assert topic.subscriber_count == 1

        assert s2.id in topic.get_subscriber_ids()
        assert s1.id not in topic.get_subscriber_ids()

        topic.shutdown()


# ── fail-to-pass: these FAIL with the bug, PASS after fix ────────────────

class TestMessageOrderingConcurrent:
    """Messages must arrive in sequence order even with concurrent dispatch."""

    @pytest.mark.fail_to_pass
    def test_message_ordering_under_concurrent_publish(self):
        """Publish 200 messages rapidly and verify they arrive in order.

        BUG: Topic dispatches each message delivery as a separate thread
        task. Thread scheduling is non-deterministic, so message N may
        arrive after message N+1.

        Run multiple times to increase chance of triggering the race.
        """
        for trial in range(5):  # Multiple trials to catch intermittent race
            Message.reset_sequence()
            Subscriber.reset_ids()

            broker = MessageBroker(default_workers=4)
            broker.create_topic("events", max_workers=4)
            sub = Subscriber(name=f"ordered_sub_{trial}")
            broker.subscribe("events", sub)

            pub = Publisher(broker, name="fast_pub")

            for i in range(200):
                pub.publish("events", f"event_{i}")

            broker.wait_all()
            broker.shutdown()

            messages = sub.drain()
            assert len(messages) == 200, (
                f"Trial {trial}: expected 200 messages, got {len(messages)}"
            )

            sequences = [m.sequence for m in messages]
            for i in range(1, len(sequences)):
                assert sequences[i] > sequences[i - 1], (
                    f"Trial {trial}: messages out of order at index {i}: "
                    f"seq {sequences[i-1]} -> {sequences[i]}"
                )


class TestMultipleSubscribersOrdered:
    """All subscribers must receive messages in order."""

    @pytest.mark.fail_to_pass
    def test_multiple_subscribers_all_ordered(self):
        """Multiple subscribers on the same topic should each receive
        messages in sequence order.
        """
        for trial in range(3):
            Message.reset_sequence()
            Subscriber.reset_ids()

            broker = MessageBroker(default_workers=4)
            broker.create_topic("multi", max_workers=4)

            subs = [Subscriber(name=f"sub_{j}_{trial}") for j in range(3)]
            for s in subs:
                broker.subscribe("multi", s)

            pub = Publisher(broker, name="multi_pub")
            for i in range(100):
                pub.publish("multi", f"data_{i}")

            broker.wait_all()
            broker.shutdown()

            for s in subs:
                messages = s.drain()
                assert len(messages) == 100, (
                    f"Trial {trial}, {s.name}: expected 100, got {len(messages)}"
                )

                sequences = [m.sequence for m in messages]
                for i in range(1, len(sequences)):
                    assert sequences[i] > sequences[i - 1], (
                        f"Trial {trial}, {s.name}: out of order at {i}: "
                        f"{sequences[i-1]} -> {sequences[i]}"
                    )


class TestOrderingWithSlowSubscriber:
    """Ordering must be maintained even when one subscriber is slow."""

    @pytest.mark.fail_to_pass
    def test_ordering_with_slow_subscriber(self):
        """A subscriber with simulated processing delay should still
        receive messages in order.
        """
        Message.reset_sequence()
        Subscriber.reset_ids()

        broker = MessageBroker(default_workers=4)
        broker.create_topic("slow_test", max_workers=4)

        class SlowSubscriber(Subscriber):
            """Subscriber that adds a tiny delay on receive."""
            def receive(self, message):
                # Tiny delay to exacerbate thread scheduling issues
                if message.sequence % 3 == 0:
                    time.sleep(0.001)
                return super().receive(message)

        sub = SlowSubscriber(name="slow_sub")
        broker.subscribe("slow_test", sub)

        pub = Publisher(broker, name="pub")
        for i in range(100):
            pub.publish("slow_test", f"item_{i}")

        broker.wait_all(timeout=10.0)
        broker.shutdown()

        messages = sub.drain()
        assert len(messages) == 100

        sequences = [m.sequence for m in messages]
        for i in range(1, len(sequences)):
            assert sequences[i] > sequences[i - 1], (
                f"Slow subscriber received out of order at {i}: "
                f"{sequences[i-1]} -> {sequences[i]}"
            )
