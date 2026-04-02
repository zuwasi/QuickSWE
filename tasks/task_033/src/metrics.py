"""MetricsCollector — records throughput and latency metrics.

Basic structure exists but needs async-compatible implementation.
TODO: Make metrics safe for concurrent async access and add timing support.
"""

import time


class MetricsCollector:
    """Collects throughput and latency metrics for the pipeline.

    Tracks:
    - Total chunks processed
    - Total bytes transferred
    - Per-chunk latency (time from read to write)
    - Throughput (chunks/second)
    """

    def __init__(self):
        self._start_time = None
        self._end_time = None
        self._chunk_count = 0
        self._total_bytes = 0
        self._latencies = []

    @property
    def chunk_count(self):
        return self._chunk_count

    @property
    def total_bytes(self):
        return self._total_bytes

    @property
    def latencies(self):
        return list(self._latencies)

    def start(self):
        """Mark the start of pipeline execution."""
        self._start_time = time.monotonic()

    def stop(self):
        """Mark the end of pipeline execution."""
        self._end_time = time.monotonic()

    def record_chunk(self, byte_count, latency=None):
        """Record a processed chunk.

        Args:
            byte_count: Number of bytes in this chunk.
            latency: Optional time in seconds for this chunk.
        """
        self._chunk_count += 1
        self._total_bytes += byte_count
        if latency is not None:
            self._latencies.append(latency)

    @property
    def elapsed(self):
        """Total elapsed time in seconds."""
        if self._start_time is None:
            return 0.0
        end = self._end_time or time.monotonic()
        return end - self._start_time

    @property
    def throughput(self):
        """Chunks per second."""
        e = self.elapsed
        if e <= 0:
            return 0.0
        return self._chunk_count / e

    @property
    def avg_latency(self):
        """Average per-chunk latency in seconds."""
        if not self._latencies:
            return 0.0
        return sum(self._latencies) / len(self._latencies)

    def reset(self):
        """Reset all metrics."""
        self._start_time = None
        self._end_time = None
        self._chunk_count = 0
        self._total_bytes = 0
        self._latencies = []

    def summary(self):
        """Return a summary dict."""
        return {
            "chunks": self._chunk_count,
            "total_bytes": self._total_bytes,
            "elapsed_seconds": self.elapsed,
            "throughput_chunks_per_sec": self.throughput,
            "avg_latency_seconds": self.avg_latency,
        }
