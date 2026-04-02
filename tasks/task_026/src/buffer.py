"""Buffer class for batching items between pipeline stages."""


class Buffer:
    """Buffers items between pipeline stages for batch processing.

    Supports configurable batch sizes and tracks the previous batch
    for debugging and stage-comparison purposes.
    """

    def __init__(self, batch_size=10):
        self._batch_size = batch_size
        self._items = []
        self._previous = None
        self._total_flushed = 0
        self._flush_count = 0

    @property
    def batch_size(self):
        return self._batch_size

    @property
    def size(self):
        return len(self._items)

    @property
    def is_full(self):
        return len(self._items) >= self._batch_size

    @property
    def is_empty(self):
        return len(self._items) == 0

    @property
    def previous_batch(self):
        """Return the previous batch for debugging/comparison."""
        return self._previous

    @property
    def total_flushed(self):
        return self._total_flushed

    @property
    def flush_count(self):
        return self._flush_count

    def add(self, item):
        """Add an item to the buffer."""
        self._items.append(item)

    def add_many(self, items):
        """Add multiple items to the buffer."""
        self._items.extend(items)

    def flush(self):
        """Flush the buffer and return all items.

        Stores the current batch as 'previous' for later comparison,
        then clears the internal buffer.
        """
        if not self._items:
            return []

        batch = list(self._items)

        # BUG: Store reference to the batch items directly.
        # Since batch is a new list but contains references to the SAME
        # dict objects, when a downstream MapStage mutates those dicts
        # in-place, self._previous will reflect the mutations too.
        # The fix would be: self._previous = [dict(item) if isinstance(item, dict) else item for item in batch]
        self._previous = batch

        self._total_flushed += len(batch)
        self._flush_count += 1
        self._items = []
        return batch

    def peek(self):
        """Look at items without flushing."""
        return list(self._items)

    def clear(self):
        """Clear the buffer without returning items."""
        self._items = []

    def drain_batches(self):
        """Generator that yields batches of batch_size until empty."""
        while len(self._items) >= self._batch_size:
            batch = self._items[:self._batch_size]
            self._previous = batch
            self._items = self._items[self._batch_size:]
            self._total_flushed += len(batch)
            self._flush_count += 1
            yield batch

    def stats(self):
        """Return buffer statistics."""
        return {
            'current_size': len(self._items),
            'batch_size': self._batch_size,
            'total_flushed': self._total_flushed,
            'flush_count': self._flush_count,
            'has_previous': self._previous is not None,
            'previous_size': len(self._previous) if self._previous else 0
        }

    def __len__(self):
        return len(self._items)

    def __repr__(self):
        return (
            f"Buffer(batch_size={self._batch_size}, "
            f"current={len(self._items)}, flushed={self._total_flushed})"
        )
