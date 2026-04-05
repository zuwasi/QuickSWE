"""Async bounded queue for producer-consumer workflows."""

import asyncio
from typing import Any, Optional


class AsyncBoundedQueue:
    """A bounded async queue that supports multiple producers and consumers.

    When the queue is full, put() should wait until space is available.
    When the queue is empty, get() should wait until an item is available.
    """

    def __init__(self, maxsize: int = 10):
        if maxsize <= 0:
            raise ValueError("maxsize must be a positive integer")
        self._maxsize = maxsize
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=maxsize)
        self._put_count = 0
        self._get_count = 0
        self._closed = False

    @property
    def maxsize(self) -> int:
        return self._maxsize

    @property
    def qsize(self) -> int:
        return self._queue.qsize()

    @property
    def empty(self) -> bool:
        return self._queue.empty()

    @property
    def full(self) -> bool:
        return self._queue.full()

    @property
    def put_count(self) -> int:
        return self._put_count

    @property
    def get_count(self) -> int:
        return self._get_count

    async def put(self, item: Any) -> bool:
        """Put an item into the queue.

        If the queue is full, this should wait until space is available.
        Returns True if the item was successfully enqueued.
        """
        if self._closed:
            raise RuntimeError("Cannot put into a closed queue")

        if self._queue.full():
            try:
                self._queue.put_nowait(item)
            except asyncio.QueueFull:
                return False
        else:
            self._queue.put_nowait(item)

        self._put_count += 1
        return True

    async def get(self, timeout: Optional[float] = None) -> Any:
        """Get an item from the queue.

        If the queue is empty, waits until an item is available.
        If timeout is specified, raises TimeoutError after that many seconds.
        """
        if self._closed and self._queue.empty():
            raise RuntimeError("Queue is closed and empty")

        if timeout is not None:
            return await asyncio.wait_for(self._queue.get(), timeout=timeout)
        return await self._queue.get()

    async def close(self) -> None:
        """Close the queue, preventing further puts."""
        self._closed = True

    async def drain(self) -> list:
        """Remove and return all items currently in the queue."""
        items = []
        while not self._queue.empty():
            try:
                items.append(self._queue.get_nowait())
                self._get_count += 1
            except asyncio.QueueEmpty:
                break
        return items

    async def put_many(self, items: list) -> int:
        """Put multiple items into the queue.

        Returns the number of items successfully enqueued.
        """
        count = 0
        for item in items:
            result = await self.put(item)
            if result:
                count += 1
        return count


async def producer(queue: AsyncBoundedQueue, items: list) -> int:
    """Produce items into the queue. Returns number of items produced."""
    produced = 0
    for item in items:
        success = await queue.put(item)
        if success:
            produced += 1
    return produced


async def consumer(queue: AsyncBoundedQueue, count: int,
                   timeout: float = 5.0) -> list:
    """Consume count items from the queue. Returns list of consumed items."""
    consumed = []
    for _ in range(count):
        try:
            item = await queue.get(timeout=timeout)
            consumed.append(item)
            queue._get_count += 1
        except (asyncio.TimeoutError, RuntimeError):
            break
    return consumed


async def run_pipeline(items: list, queue_size: int = 5,
                       num_consumers: int = 1) -> list:
    """Run a producer-consumer pipeline and return all consumed items."""
    queue = AsyncBoundedQueue(maxsize=queue_size)
    items_per_consumer = len(items) // num_consumers

    consumer_tasks = []
    for i in range(num_consumers):
        count = items_per_consumer
        if i == num_consumers - 1:
            count = len(items) - items_per_consumer * (num_consumers - 1)
        consumer_tasks.append(
            asyncio.create_task(consumer(queue, count, timeout=2.0))
        )

    await producer(queue, items)
    await queue.close()

    results = []
    for task in consumer_tasks:
        results.extend(await task)
    return results
