"""FileReader — reads data in chunks.

Has a synchronous read_chunk() method that works.
TODO: Add async read_chunk_async() for use in the async pipeline.
"""

import io


class FileReader:
    """Reads data from a source in fixed-size chunks.

    Attributes:
        _source: A file-like object or bytes to read from.
        _chunk_size: Number of bytes per chunk.
        _position: Current read position.
        _total_read: Total bytes read so far.
    """

    def __init__(self, source, chunk_size=1024):
        """Initialize the reader.

        Args:
            source: bytes, bytearray, or file-like object to read from.
            chunk_size: Size of each chunk in bytes.
        """
        if isinstance(source, (bytes, bytearray)):
            self._source = io.BytesIO(source)
        else:
            self._source = source
        self._chunk_size = chunk_size
        self._position = 0
        self._total_read = 0
        self._exhausted = False

    @property
    def chunk_size(self):
        return self._chunk_size

    @property
    def total_read(self):
        return self._total_read

    @property
    def exhausted(self):
        return self._exhausted

    def read_chunk(self):
        """Read the next chunk synchronously.

        Returns:
            bytes: The chunk data, or None if exhausted.
        """
        if self._exhausted:
            return None
        data = self._source.read(self._chunk_size)
        if not data:
            self._exhausted = True
            return None
        self._total_read += len(data)
        self._position += len(data)
        return data

    def read_all_chunks(self):
        """Read all remaining chunks and return as a list."""
        chunks = []
        while True:
            chunk = self.read_chunk()
            if chunk is None:
                break
            chunks.append(chunk)
        return chunks

    def reset(self, new_source=None):
        """Reset the reader, optionally with a new source."""
        if new_source is not None:
            if isinstance(new_source, (bytes, bytearray)):
                self._source = io.BytesIO(new_source)
            else:
                self._source = new_source
        elif hasattr(self._source, 'seek'):
            self._source.seek(0)
        self._position = 0
        self._total_read = 0
        self._exhausted = False
