class Inventory:
    """A simple inventory management system."""

    def __init__(self):
        self._items = {}

    def add_item(self, name, quantity, price):
        """Add an item to the inventory.

        Args:
            name: Item name (string, used as unique key).
            quantity: Number of units (int).
            price: Price per unit (float).
        """
        self._items[name] = {
            "name": name,
            "quantity": quantity,
            "price": price,
        }

    def remove_item(self, name):
        """Remove an item by name. Raises KeyError if not found."""
        if name not in self._items:
            raise KeyError(f"Item '{name}' not found in inventory")
        del self._items[name]

    def get_item(self, name):
        """Get an item by exact name. Returns dict or None."""
        item = self._items.get(name)
        if item is not None:
            return dict(item)
        return None
