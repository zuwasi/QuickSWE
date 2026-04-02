"""FileWriter — writes processed data chunks.

Has a synchronous write_chunk() method that works.
TODO: Add async write_chunk_async() for use in the async pipeline.
"""

import io


class FileWriter:
    """Writes data chunks to a destination.

    Attributes:
        _dest: A file-like object to write to.
        _written_count: Number of chunks written.
        _total_written: Total bytes written.
    """

    def __init__(self, dest=None):
        """Initialize the writer.

        Args:
            dest: File-like object to write to. If None, uses an internal BytesIO.
        """
        self._dest = dest or io.BytesIO()
        self._written_count = 0
        self._total_written = 0

    @property
    def written_count(self):
        return self._written_count

    @property
    def total_written(self):
        return self._total_written

    def write_chunk(self, data):
        """Write a chunk synchronously.

        Args:
            data: bytes to write.

        Returns:
            int: Number of bytes written.
        """
        if data is None:
            return 0
        n = self._dest.write(data)
        self._written_count += 1
        self._total_written += n
        return n

    def get_output(self):
        """Return all written data (only works with BytesIO dest)."""
        if hasattr(self._dest, 'getvalue'):
            return self._dest.getvalue()
        return None

    def reset(self, new_dest=None):
        """Reset the writer."""
        self._dest = new_dest or io.BytesIO()
        self._written_count = 0
        self._total_written = 0
