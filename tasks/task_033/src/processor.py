"""DataProcessor — processes data chunks.

Has a synchronous process_chunk() method that works.
TODO: Add async process_chunk_async() for use in the async pipeline.
"""


class DataProcessor:
    """Processes data chunks by applying a transformation.

    Attributes:
        _transform: A callable(bytes) -> bytes transformation.
        _processed_count: Number of chunks processed.
        _total_bytes: Total bytes processed.
    """

    def __init__(self, transform=None):
        """Initialize the processor.

        Args:
            transform: Optional transformation function. Default is identity (passthrough).
        """
        self._transform = transform or (lambda data: data)
        self._processed_count = 0
        self._total_bytes = 0

    @property
    def processed_count(self):
        return self._processed_count

    @property
    def total_bytes(self):
        return self._total_bytes

    def process_chunk(self, data):
        """Process a single chunk synchronously.

        Args:
            data: bytes to process.

        Returns:
            bytes: Transformed data.
        """
        if data is None:
            return None
        result = self._transform(data)
        self._processed_count += 1
        self._total_bytes += len(data)
        return result

    def process_all(self, chunks):
        """Process a list of chunks and return results."""
        return [self.process_chunk(c) for c in chunks]

    def reset(self):
        """Reset processor counters."""
        self._processed_count = 0
        self._total_bytes = 0
