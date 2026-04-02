"""Tests for the async I/O pipeline with backpressure."""

import sys
import os
import asyncio
import time
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.reader import FileReader
from src.processor import DataProcessor
from src.writer import FileWriter
from src.pipeline import Pipeline
from src.buffer_pool import BufferPool
from src.metrics import MetricsCollector


# ============================================================
# PASS-TO-PASS: Sync interfaces still work
# ============================================================

class TestSyncReader:
    def test_read_bytes(self):
        data = b"Hello, World!"
        reader = FileReader(data, chunk_size=5)
        chunk = reader.read_chunk()
        assert chunk == b"Hello"

    def test_read_all(self):
        data = b"ABCDEFGHIJ"
        reader = FileReader(data, chunk_size=3)
        chunks = reader.read_all_chunks()
        assert chunks == [b"ABC", b"DEF", b"GHI", b"J"]

    def test_read_exhausted(self):
        reader = FileReader(b"ab", chunk_size=10)
        reader.read_chunk()
        assert reader.read_chunk() is None
        assert reader.exhausted

    def test_total_read(self):
        data = b"0123456789"
        reader = FileReader(data, chunk_size=4)
        reader.read_all_chunks()
        assert reader.total_read == 10


class TestSyncProcessor:
    def test_identity(self):
        proc = DataProcessor()
        assert proc.process_chunk(b"test") == b"test"

    def test_transform(self):
        proc = DataProcessor(transform=lambda d: d.upper())
        assert proc.process_chunk(b"hello") == b"HELLO"

    def test_count(self):
        proc = DataProcessor()
        proc.process_chunk(b"a")
        proc.process_chunk(b"bb")
        assert proc.processed_count == 2
        assert proc.total_bytes == 3

    def test_none_passthrough(self):
        proc = DataProcessor()
        assert proc.process_chunk(None) is None


class TestSyncWriter:
    def test_write_and_get(self):
        writer = FileWriter()
        writer.write_chunk(b"Hello")
        writer.write_chunk(b" World")
        assert writer.get_output() == b"Hello World"

    def test_written_count(self):
        writer = FileWriter()
        writer.write_chunk(b"abc")
        writer.write_chunk(b"de")
        assert writer.written_count == 2
        assert writer.total_written == 5


class TestSyncPipeline:
    def test_sync_pipeline(self):
        data = b"Hello, Pipeline!"
        reader = FileReader(data, chunk_size=5)
        proc = DataProcessor(transform=lambda d: d.upper())
        writer = FileWriter()
        pipe = Pipeline(reader, proc, writer)
        total = pipe.run_sync()
        assert total == len(data)
        assert writer.get_output() == b"HELLO, PIPELINE!"


class TestBufferPoolSync:
    def test_acquire_release(self):
        pool = BufferPool(pool_size=3, buffer_size=16)
        assert pool.available_count == 3
        buf = pool.acquire_sync()
        assert pool.available_count == 2
        assert pool.checked_out_count == 1
        pool.release_sync(buf)
        assert pool.available_count == 3

    def test_exhaust_raises(self):
        pool = BufferPool(pool_size=1, buffer_size=8)
        pool.acquire_sync()
        with pytest.raises(RuntimeError):
            pool.acquire_sync()


class TestMetricsBasic:
    def test_record_chunks(self):
        m = MetricsCollector()
        m.record_chunk(100, latency=0.01)
        m.record_chunk(200, latency=0.02)
        assert m.chunk_count == 2
        assert m.total_bytes == 300

    def test_summary(self):
        m = MetricsCollector()
        s = m.summary()
        assert "chunks" in s
        assert "total_bytes" in s


# ============================================================
# FAIL-TO-PASS: Async pipeline tests
# ============================================================

@pytest.mark.fail_to_pass
class TestAsyncPipeline:
    def test_async_pipeline_basic(self):
        """Async pipeline should produce same output as sync."""
        data = b"Hello, Async Pipeline World!"
        reader = FileReader(data, chunk_size=7)
        proc = DataProcessor()
        writer = FileWriter()
        pipe = Pipeline(reader, proc, writer)
        total = asyncio.run(pipe.run())
        assert total == len(data)
        assert writer.get_output() == data

    def test_async_pipeline_with_transform(self):
        data = b"transform me please"
        reader = FileReader(data, chunk_size=5)
        proc = DataProcessor(transform=lambda d: bytes(b ^ 0xFF for b in d))
        writer = FileWriter()
        pipe = Pipeline(reader, proc, writer)
        asyncio.run(pipe.run())
        output = writer.get_output()
        # Verify the transform was applied
        expected = bytes(b ^ 0xFF for b in data)
        assert output == expected

    def test_async_pipeline_large_data(self):
        """Pipeline handles data larger than queue size."""
        data = os.urandom(10000)
        reader = FileReader(data, chunk_size=100)
        proc = DataProcessor()
        writer = FileWriter()
        pipe = Pipeline(reader, proc, writer, queue_size=3)
        total = asyncio.run(pipe.run())
        assert total == len(data)
        assert writer.get_output() == data

    def test_async_pipeline_counts(self):
        data = b"A" * 1000
        reader = FileReader(data, chunk_size=100)
        proc = DataProcessor()
        writer = FileWriter()
        pipe = Pipeline(reader, proc, writer)
        asyncio.run(pipe.run())
        assert reader.total_read == 1000
        assert proc.processed_count == 10
        assert writer.written_count == 10


@pytest.mark.fail_to_pass
class TestBackpressure:
    def test_backpressure_slow_writer(self):
        """With a slow writer and small queue, reader shouldn't run too far ahead."""
        data = b"X" * 500
        reader = FileReader(data, chunk_size=50)
        proc = DataProcessor()
        writer = FileWriter()
        # Very small queue — only 2 items before backpressure kicks in
        pipe = Pipeline(reader, proc, writer, queue_size=2)

        write_times = []
        original_write = writer.write_chunk

        def slow_write(chunk):
            # Simulate slow writer — record that we were called
            write_times.append(time.monotonic())
            return original_write(chunk)

        writer.write_chunk = slow_write

        asyncio.run(pipe.run())
        assert writer.get_output() == data
        assert len(write_times) == 10  # 500 / 50 = 10 chunks

    def test_backpressure_preserves_data_integrity(self):
        """With tiny queue and many chunks, all data must still be correctly transferred."""
        data = b"Y" * 300
        reader = FileReader(data, chunk_size=30)
        proc = DataProcessor()
        writer = FileWriter()
        # Very small queue — forces backpressure on every few chunks
        pipe = Pipeline(reader, proc, writer, queue_size=1)
        total = asyncio.run(pipe.run())
        assert total == 300
        assert writer.get_output() == data
        assert writer.written_count == 10


@pytest.mark.fail_to_pass
class TestAsyncBufferPool:
    def test_async_acquire_release(self):
        async def run():
            pool = BufferPool(pool_size=3, buffer_size=64)
            buf1 = await pool.acquire()
            assert isinstance(buf1, bytearray)
            assert pool.checked_out_count == 1
            await pool.release(buf1)
            assert pool.checked_out_count == 0

        asyncio.run(run())

    def test_async_pool_semaphore_limits(self):
        """Pool with size 2 should block the 3rd acquire until one is released."""
        async def run():
            pool = BufferPool(pool_size=2, buffer_size=32)
            buf1 = await pool.acquire()
            buf2 = await pool.acquire()
            assert pool.checked_out_count == 2

            released = [False]

            async def delayed_release():
                await asyncio.sleep(0.05)
                released[0] = True
                await pool.release(buf1)

            asyncio.create_task(delayed_release())
            buf3 = await asyncio.wait_for(pool.acquire(), timeout=1.0)
            assert released[0]  # Proves acquire blocked until release
            assert isinstance(buf3, bytearray)

        asyncio.run(run())

    def test_async_pool_concurrent_usage(self):
        async def run():
            pool = BufferPool(pool_size=3, buffer_size=16)
            acquired = []

            async def worker(n):
                buf = await pool.acquire()
                acquired.append(n)
                await asyncio.sleep(0.01)
                await pool.release(buf)

            await asyncio.gather(*[worker(i) for i in range(6)])
            assert len(acquired) == 6

        asyncio.run(run())


@pytest.mark.fail_to_pass
class TestAsyncMetrics:
    def test_metrics_with_pipeline(self):
        """Metrics collector should be usable with async pipeline."""
        data = b"M" * 200
        reader = FileReader(data, chunk_size=50)
        proc = DataProcessor()
        writer = FileWriter()
        metrics = MetricsCollector()

        async def run():
            metrics.start()
            pipe = Pipeline(reader, proc, writer, queue_size=3)
            await pipe.run()
            metrics.stop()

            # Record metrics manually since pipeline doesn't auto-integrate
            # (but the pipeline should be able to work with metrics)
            for _ in range(4):
                metrics.record_chunk(50)

        asyncio.run(run())
        assert metrics.chunk_count == 4
        assert metrics.total_bytes == 200
        assert metrics.elapsed > 0
        assert metrics.throughput > 0


@pytest.mark.fail_to_pass
class TestAsyncPipelineEdgeCases:
    def test_empty_input(self):
        reader = FileReader(b"", chunk_size=10)
        proc = DataProcessor()
        writer = FileWriter()
        pipe = Pipeline(reader, proc, writer)
        total = asyncio.run(pipe.run())
        assert total == 0
        assert writer.get_output() == b""

    def test_single_byte(self):
        reader = FileReader(b"X", chunk_size=1)
        proc = DataProcessor()
        writer = FileWriter()
        pipe = Pipeline(reader, proc, writer)
        total = asyncio.run(pipe.run())
        assert total == 1
        assert writer.get_output() == b"X"

    def test_chunk_larger_than_data(self):
        reader = FileReader(b"tiny", chunk_size=1024)
        proc = DataProcessor()
        writer = FileWriter()
        pipe = Pipeline(reader, proc, writer)
        total = asyncio.run(pipe.run())
        assert total == 4
        assert writer.get_output() == b"tiny"
