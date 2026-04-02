"""Doubly-linked list implementation for LRU cache."""


class Node:
    """A node in a doubly-linked list."""

    __slots__ = ('key', 'value', 'prev', 'next')

    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.prev = None
        self.next = None

    def __repr__(self):
        return f"Node({self.key!r}: {self.value!r})"


class DoublyLinkedList:
    """Doubly-linked list supporting O(1) insertion and removal.

    Used by the LRU cache to maintain access order.
    Head = most recently used, Tail = least recently used.
    """

    def __init__(self):
        self.head = None
        self.tail = None
        self._size = 0

    @property
    def size(self):
        return self._size

    @property
    def is_empty(self):
        return self._size == 0

    def push_front(self, node):
        """Add a node at the front (head) of the list."""
        node.prev = None
        node.next = self.head

        if self.head is not None:
            self.head.prev = node

        self.head = node

        if self.tail is None:
            self.tail = node

        self._size += 1

    def remove(self, node):
        """Remove a node from the list."""
        if node.prev:
            node.prev.next = node.next
        else:
            self.head = node.next

        if node.next:
            node.next.prev = node.prev
        else:
            self.tail = node.prev

        node.prev = None
        node.next = None
        self._size -= 1

    def remove_tail(self):
        """Remove and return the tail node (least recently used)."""
        if self.tail is None:
            return None

        node = self.tail
        self.remove(node)
        return node

    def move_to_front(self, node):
        """Move an existing node to the front of the list.

        BUG: When the node is already at the head, we return early.
        This is correct for the common case, BUT there is a subtle issue:
        the tail pointer is not updated when needed.

        Specifically, when we move a node that IS the tail to the front,
        we need to update self.tail to point to the node's predecessor.
        The remove() call handles this correctly. But there's a bug below
        in how we handle the two-element case.
        """
        if node is self.head:
            return

        # Detach node from its current position
        # BUG: We manually detach instead of calling self.remove()
        # to "optimize" by not decrementing _size. But we forget
        # to update self.tail when the node being moved IS the tail.
        if node.prev:
            node.prev.next = node.next
        if node.next:
            node.next.prev = node.prev

        # BUG: Missing tail update! If node is the tail,
        # self.tail should be set to node.prev.
        # Without this, self.tail still points to the moved node,
        # which is now at the head. So when we later call remove_tail()
        # to evict, we remove the HEAD (most recently used) instead
        # of the actual tail (least recently used).

        # Attach at front
        node.prev = None
        node.next = self.head
        if self.head:
            self.head.prev = node
        self.head = node

    def peek_front(self):
        """Return the head node without removing it."""
        return self.head

    def peek_tail(self):
        """Return the tail node without removing it."""
        return self.tail

    def to_list(self):
        """Convert to a Python list (head to tail order)."""
        result = []
        current = self.head
        while current:
            result.append(current)
            current = current.next
        return result

    def keys(self):
        """Return keys in order from head (MRU) to tail (LRU)."""
        return [node.key for node in self.to_list()]

    def __len__(self):
        return self._size

    def __repr__(self):
        keys = self.keys()
        return f"DoublyLinkedList({keys})"
