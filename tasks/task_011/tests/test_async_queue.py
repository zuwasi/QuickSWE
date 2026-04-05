import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import asyncio
from src.async_queue import AsyncBoundedQueue, producer, consumer, run_pipeline


def _run(coro):
    """Helper to run async tests without pytest-asyncio."""
    return asyncio.run(coro)


# ─── fail_to_pass ───────────────────────────────────────────────

@pytest.mark.fail_to_pass
def test_put_waits_when_full():
    """put() must block (not drop) when the queue is full."""
    async def _test():
        q = AsyncBoundedQueue(maxsize=2)
        await q.put("a")
        await q.put("b")
        assert q.full

        received = []

        async def delayed_consumer():
            await asyncio.sleep(0.1)
            received.append(await q.get())

        consumer_task = asyncio.create_task(delayed_consumer())
        result = await asyncio.wait_for(q.put("c"), timeout=1.0)
        await consumer_task

        assert result is True
        assert q.put_count == 3

    _run(_test())


@pytest.mark.fail_to_pass
def test_no_messages_dropped_under_load():
    """All messages from a fast producer must be received."""
    async def _test():
        q = AsyncBoundedQueue(maxsize=3)
        items = list(range(20))

        async def slow_consumer(n):
            out = []
            for _ in range(n):
                out.append(await q.get(timeout=3.0))
                await asyncio.sleep(0.01)
            return out

        cons = asyncio.create_task(slow_consumer(20))
        produced = await producer(q, items)
        result = await cons

        assert produced == 20
        assert sorted(result) == items

    _run(_test())


@pytest.mark.fail_to_pass
def test_put_many_enqueues_all():
    """put_many must enqueue every item, even when queue fills up."""
    async def _test():
        q = AsyncBoundedQueue(maxsize=2)

        async def drain_later():
            await asyncio.sleep(0.05)
            return await q.drain()

        drainer = asyncio.create_task(drain_later())
        count = await asyncio.wait_for(q.put_many([1, 2, 3, 4, 5]), timeout=2.0)
        remaining = await drainer

        assert count == 5

    _run(_test())


@pytest.mark.fail_to_pass
def test_pipeline_preserves_all_items():
    """run_pipeline must deliver every produced item to consumers."""
    async def _test():
        items = list(range(15))
        result = await run_pipeline(items, queue_size=3, num_consumers=2)
        assert sorted(result) == items

    _run(_test())


# ─── pass_to_pass ───────────────────────────────────────────────

def test_basic_put_get():
    """Simple put then get works."""
    async def _test():
        q = AsyncBoundedQueue(maxsize=5)
        await q.put("hello")
        val = await q.get(timeout=1.0)
        assert val == "hello"

    _run(_test())


def test_queue_properties():
    """Properties report correct state."""
    async def _test():
        q = AsyncBoundedQueue(maxsize=3)
        assert q.maxsize == 3
        assert q.empty
        assert not q.full
        await q.put(1)
        assert q.qsize == 1

    _run(_test())


def test_close_prevents_put():
    """After close(), put() raises RuntimeError."""
    async def _test():
        q = AsyncBoundedQueue(maxsize=5)
        await q.close()
        with pytest.raises(RuntimeError):
            await q.put("x")

    _run(_test())
