"""Dispatcher that sets up event routing through the bus."""

from .event_bus import Event, EventBus
from .handlers import (
    OrderHandler,
    InventoryHandler,
    NotificationHandler,
    AuditHandler,
)


class Dispatcher:
    """Routes domain events through the event bus by wiring up handlers."""

    def __init__(self):
        self.bus = EventBus()
        self.order_handler = OrderHandler()
        self.inventory_handler = InventoryHandler()
        self.notification_handler = NotificationHandler()
        self.audit_handler = AuditHandler()

    def setup_routes(self, include_audit=False):
        """Wire up all event handlers.

        Args:
            include_audit: If True, also register the audit handler
                          (which can cause problems with certain event chains).
        """
        # Order events
        self.bus.subscribe("order.placed", self.order_handler.on_order_placed)
        self.bus.subscribe("order.placed", self.notification_handler.on_order_placed)

        # Inventory events
        self.bus.subscribe(
            "inventory.check_requested",
            self.inventory_handler.on_inventory_check,
        )
        self.bus.subscribe(
            "inventory.checked",
            self.inventory_handler.on_inventory_checked,
        )

        # Shipping events
        self.bus.subscribe(
            "shipping.requested",
            self.notification_handler.on_shipping_requested,
        )

        # Payment events
        self.bus.subscribe(
            "payment.confirmed",
            self.order_handler.on_payment_confirmed,
        )

        # Audit (this creates the circular dependency)
        if include_audit:
            self.bus.subscribe(
                "inventory.checked",
                self.audit_handler.on_any_inventory_event,
            )

    def dispatch(self, event_type: str, payload: dict = None) -> list:
        """Dispatch an event through the bus.

        Args:
            event_type: The type of event to dispatch.
            payload: Optional event payload.

        Returns:
            List of handler results.
        """
        event = Event(
            event_type=event_type,
            payload=payload or {},
            source="Dispatcher",
        )
        return self.bus.publish(event)
