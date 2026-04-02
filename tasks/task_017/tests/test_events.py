import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.event_bus import Event, EventBus
from src.handlers import (
    OrderHandler,
    InventoryHandler,
    NotificationHandler,
    AuditHandler,
)
from src.dispatcher import Dispatcher


# ── pass-to-pass: basic event bus functionality ───────────────────


class TestEventBusBasic:
    def test_subscribe_and_publish(self):
        bus = EventBus()
        received = []
        bus.subscribe("test", lambda e, b: received.append(e))
        bus.publish(Event(event_type="test", payload={"x": 1}))
        assert len(received) == 1
        assert received[0].payload == {"x": 1}

    def test_multiple_subscribers(self):
        bus = EventBus()
        results = []
        bus.subscribe("test", lambda e, b: results.append("a"))
        bus.subscribe("test", lambda e, b: results.append("b"))
        bus.publish(Event(event_type="test"))
        assert results == ["a", "b"]

    def test_unsubscribe(self):
        bus = EventBus()
        handler = lambda e, b: None
        bus.subscribe("test", handler)
        assert bus.get_subscriber_count("test") == 1
        bus.unsubscribe("test", handler)
        assert bus.get_subscriber_count("test") == 0

    def test_publish_no_subscribers(self):
        bus = EventBus()
        results = bus.publish(Event(event_type="nobody_listens"))
        assert results == []

    def test_event_log(self):
        bus = EventBus()
        bus.publish(Event(event_type="a"))
        bus.publish(Event(event_type="b"))
        log = bus.get_event_log()
        assert len(log) == 2
        assert log[0].event_type == "a"

    def test_clear_log(self):
        bus = EventBus()
        bus.publish(Event(event_type="a"))
        bus.clear_log()
        assert len(bus.get_event_log()) == 0

    def test_no_duplicate_subscribe(self):
        bus = EventBus()
        handler = lambda e, b: None
        bus.subscribe("test", handler)
        bus.subscribe("test", handler)
        assert bus.get_subscriber_count("test") == 1


class TestDispatcherNormalFlow:
    def test_order_flow_without_audit(self):
        """Normal order flow without audit handler should complete."""
        dispatcher = Dispatcher()
        dispatcher.setup_routes(include_audit=False)
        dispatcher.dispatch("order.placed", {"order_id": "ORD-001"})

        # Order handler should have processed the event
        assert len(dispatcher.order_handler.processed_events) >= 1
        # Notification should have been sent
        assert len(dispatcher.notification_handler.notifications_sent) >= 1

    def test_payment_triggers_shipping(self):
        dispatcher = Dispatcher()
        dispatcher.setup_routes(include_audit=False)
        dispatcher.dispatch("payment.confirmed", {"order_id": "ORD-002"})
        notifs = dispatcher.notification_handler.notifications_sent
        assert any(n["type"] == "shipping" for n in notifs)

    def test_isolated_event_types(self):
        """Events of one type don't trigger handlers for other types."""
        dispatcher = Dispatcher()
        dispatcher.setup_routes(include_audit=False)
        dispatcher.dispatch("shipping.requested", {"order_id": "ORD-003"})
        assert len(dispatcher.order_handler.processed_events) == 0


class TestHandlersUnit:
    def test_notification_handler_records(self):
        handler = NotificationHandler()
        bus = EventBus()
        event = Event(event_type="shipping.requested", payload={"order_id": "1"})
        handler.on_shipping_requested(event, bus)
        assert len(handler.notifications_sent) == 1

    def test_audit_handler_logs(self):
        handler = AuditHandler()
        bus = EventBus()
        event = Event(event_type="inventory.checked", payload={"order_id": "1"})
        # Don't subscribe the audit handler to bus to avoid recursion in unit test
        handler.audit_log.append(event)
        assert len(handler.audit_log) == 1


# ── fail-to-pass: circular event chain must be detected ──────────


class TestCircularEventDetection:
    @pytest.mark.fail_to_pass
    def test_circular_chain_does_not_hang(self):
        """When audit handler creates a circular event chain,
        the system should detect it and stop, not hang."""
        dispatcher = Dispatcher()
        dispatcher.setup_routes(include_audit=True)

        # This should NOT cause infinite recursion / hang.
        # The event bus should detect the re-entrant publish and either
        # raise a clear error or enforce a max depth.
        try:
            dispatcher.dispatch("order.placed", {"order_id": "ORD-CIRC"})
        except RecursionError:
            pytest.fail(
                "EventBus should handle circular event chains gracefully "
                "instead of raising RecursionError"
            )

    @pytest.mark.fail_to_pass
    def test_direct_circular_handlers(self):
        """Two handlers that directly trigger each other's events
        should be caught by re-entrancy protection."""
        bus = EventBus()

        def handler_a(event, b):
            b.publish(Event(event_type="event_b", payload={"depth": "a"}))

        def handler_b(event, b):
            b.publish(Event(event_type="event_a", payload={"depth": "b"}))

        bus.subscribe("event_a", handler_a)
        bus.subscribe("event_b", handler_b)

        try:
            bus.publish(Event(event_type="event_a"))
        except RecursionError:
            pytest.fail(
                "EventBus should detect circular publish chains "
                "instead of hitting RecursionError"
            )

    @pytest.mark.fail_to_pass
    def test_max_depth_enforced(self):
        """The event bus should enforce a maximum publish depth."""
        bus = EventBus()
        call_count = 0

        def recursive_handler(event, b):
            nonlocal call_count
            call_count += 1
            b.publish(Event(event_type="self_loop"))

        bus.subscribe("self_loop", recursive_handler)

        try:
            bus.publish(Event(event_type="self_loop"))
        except RecursionError:
            pytest.fail("Should enforce max depth instead of RecursionError")

        # Should have stopped well before Python's recursion limit (~1000)
        assert call_count <= 50, (
            f"Expected max depth enforcement, but handler ran {call_count} times"
        )
