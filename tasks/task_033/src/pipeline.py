"""Pipeline — connects Reader, Processor, and Writer.

Synchronous pipeline works: read all -> process all -> write all.
TODO: Add async run() that runs stages as concurrent asyncio tasks with
      backpressure via bounded asyncio.Queues.
"""

from .reader import FileReader
from .processor import DataProcessor
from .writer import FileWriter


class Pipeline:
    """Data processing pipeline.

    Connects a reader, processor, and writer in sequence.
    Synchronous run_sync() works. Async run() needs implementation.
    """

    def __init__(self, reader, processor, writer, queue_size=5):
        """Initialize the pipeline.

        Args:
            reader: FileReader instance.
            processor: DataProcessor instance.
            writer: FileWriter instance.
            queue_size: Max size for async queues (backpressure threshold).
        """
        self._reader = reader
        self._processor = processor
        self._writer = writer
        self._queue_size = queue_size

    @property
    def reader(self):
        return self._reader

    @property
    def processor(self):
        return self._processor

    @property
    def writer(self):
        return self._writer

    def run_sync(self):
        """Run the pipeline synchronously: read all, process all, write all.

        Returns:
            int: Total bytes written.
        """
        total = 0
        while True:
            chunk = self._reader.read_chunk()
            if chunk is None:
                break
            processed = self._processor.process_chunk(chunk)
            total += self._writer.write_chunk(processed)
        return total

    async def run(self):
        """Run the pipeline asynchronously with concurrent stages and backpressure.

        Uses asyncio.Queue between stages. Reader puts chunks on read_queue,
        Processor takes from read_queue and puts on write_queue,
        Writer takes from write_queue and writes.

        None sentinel signals end-of-stream.

        Returns:
            int: Total bytes written.
        """
        # TODO: Implement async pipeline with backpressure
        raise NotImplementedError("Pipeline.run() async is not yet implemented")
