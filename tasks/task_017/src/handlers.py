"""Event handlers for the application domain."""

from .event_bus import Event, EventBus


class OrderHandler:
    """Handles order-related events."""

    def __init__(self):
        self.processed_events = []

    def on_order_placed(self, event: Event, bus: EventBus):
        """When an order is placed, trigger inventory check."""
        self.processed_events.append(event)
        bus.publish(Event(
            event_type="inventory.check_requested",
            payload={"order_id": event.payload.get("order_id")},
            source="OrderHandler",
        ))
        return {"status": "order_processed"}

    def on_payment_confirmed(self, event: Event, bus: EventBus):
        """When payment is confirmed, trigger shipping."""
        self.processed_events.append(event)
        bus.publish(Event(
            event_type="shipping.requested",
            payload={"order_id": event.payload.get("order_id")},
            source="OrderHandler",
        ))
        return {"status": "shipping_triggered"}


class InventoryHandler:
    """Handles inventory-related events."""

    def __init__(self):
        self.processed_events = []
        self._stock = {}

    def set_stock(self, item_id: str, quantity: int):
        self._stock[item_id] = quantity

    def on_inventory_check(self, event: Event, bus: EventBus):
        """When inventory check is requested, verify stock and respond."""
        self.processed_events.append(event)
        order_id = event.payload.get("order_id")
        # Publish the result back
        bus.publish(Event(
            event_type="inventory.checked",
            payload={"order_id": order_id, "in_stock": True},
            source="InventoryHandler",
        ))
        return {"status": "checked"}

    def on_inventory_checked(self, event: Event, bus: EventBus):
        """When inventory is confirmed, trigger payment processing."""
        self.processed_events.append(event)
        if event.payload.get("in_stock"):
            bus.publish(Event(
                event_type="payment.process_requested",
                payload={"order_id": event.payload.get("order_id")},
                source="InventoryHandler",
            ))
        return {"status": "payment_requested"}


class NotificationHandler:
    """Handles notification events."""

    def __init__(self):
        self.notifications_sent = []

    def on_shipping_requested(self, event: Event, bus: EventBus):
        """Send notification when shipping is requested."""
        self.notifications_sent.append({
            "type": "shipping",
            "order_id": event.payload.get("order_id"),
        })
        return {"status": "notified"}

    def on_order_placed(self, event: Event, bus: EventBus):
        """Send confirmation notification when order is placed."""
        self.notifications_sent.append({
            "type": "order_confirmation",
            "order_id": event.payload.get("order_id"),
        })
        return {"status": "notified"}


class AuditHandler:
    """Handles audit logging by re-publishing events for cross-reference.

    This handler is the problematic one — it re-publishes events that
    can create circular chains when combined with other handlers.
    """

    def __init__(self):
        self.audit_log = []

    def on_any_inventory_event(self, event: Event, bus: EventBus):
        """Audit inventory events by re-publishing an audit event."""
        self.audit_log.append(event)
        # Publishes an audit event that triggers further processing
        bus.publish(Event(
            event_type="inventory.check_requested",
            payload={**event.payload, "audit": True},
            source="AuditHandler",
        ))
        return {"status": "audited"}
