"""BufferPool — manages reusable byte buffers.

Synchronous version works.
TODO: Add async acquire/release using asyncio.Semaphore for backpressure.
"""


class BufferPool:
    """Pool of reusable byte buffers.

    Limits the number of concurrently checked-out buffers.
    Sync methods work. Async methods need implementation.
    """

    def __init__(self, pool_size=10, buffer_size=4096):
        """Initialize the buffer pool.

        Args:
            pool_size: Maximum number of buffers in the pool.
            buffer_size: Size of each buffer in bytes.
        """
        self._pool_size = pool_size
        self._buffer_size = buffer_size
        self._available = [bytearray(buffer_size) for _ in range(pool_size)]
        self._checked_out = 0

    @property
    def pool_size(self):
        return self._pool_size

    @property
    def buffer_size(self):
        return self._buffer_size

    @property
    def available_count(self):
        return len(self._available)

    @property
    def checked_out_count(self):
        return self._checked_out

    def acquire_sync(self):
        """Acquire a buffer synchronously.

        Returns:
            bytearray: A buffer from the pool.

        Raises:
            RuntimeError: If no buffers available.
        """
        if not self._available:
            raise RuntimeError("No buffers available in pool")
        buf = self._available.pop()
        self._checked_out += 1
        return buf

    def release_sync(self, buf):
        """Release a buffer back to the pool synchronously."""
        for i in range(len(buf)):
            buf[i] = 0
        self._available.append(buf)
        self._checked_out -= 1

    async def acquire(self):
        """Acquire a buffer asynchronously. Waits if pool is exhausted.

        Returns:
            bytearray: A buffer from the pool.
        """
        # TODO: Implement using asyncio.Semaphore
        raise NotImplementedError("BufferPool.acquire() async is not yet implemented")

    async def release(self, buf):
        """Release a buffer back to the pool asynchronously."""
        # TODO: Implement
        raise NotImplementedError("BufferPool.release() async is not yet implemented")
