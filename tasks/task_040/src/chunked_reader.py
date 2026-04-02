"""
Chunked file reader for processing large files.
Reads files in fixed-size byte chunks for memory efficiency.
"""

import io


class ChunkedReader:
    """Reads a file (or byte stream) in fixed-size byte chunks.

    This is designed for processing large files without loading
    the entire file into memory.
    """

    def __init__(self, source, chunk_size=4096):
        """Initialize the chunked reader.

        Args:
            source: A file path (str), bytes object, or file-like object.
            chunk_size: Size of each chunk in bytes.
        """
        self.chunk_size = chunk_size
        self._chunks_read = 0
        self._total_bytes = 0
        self._finished = False

        if isinstance(source, str):
            # File path
            self._stream = open(source, "rb")
            self._owns_stream = True
        elif isinstance(source, bytes):
            self._stream = io.BytesIO(source)
            self._owns_stream = True
        elif hasattr(source, "read"):
            self._stream = source
            self._owns_stream = False
        else:
            raise TypeError(f"Unsupported source type: {type(source)}")

    def read_chunk(self):
        """Read the next chunk of bytes.

        Returns bytes or None if EOF.

        BUG: Returns exactly chunk_size bytes regardless of character
        boundaries. A multi-byte UTF-8 character may be split across
        two chunks, causing the decoder to fail or produce garbled output.
        """
        if self._finished:
            return None

        chunk = self._stream.read(self.chunk_size)
        if not chunk:
            self._finished = True
            return None

        self._chunks_read += 1
        self._total_bytes += len(chunk)

        if len(chunk) < self.chunk_size:
            self._finished = True

        return chunk

    def read_all_chunks(self):
        """Read all chunks and return as a list of byte strings."""
        chunks = []
        while True:
            chunk = self.read_chunk()
            if chunk is None:
                break
            chunks.append(chunk)
        return chunks

    def close(self):
        """Close the underlying stream if owned."""
        if self._owns_stream and hasattr(self._stream, "close"):
            self._stream.close()

    @property
    def chunks_read(self):
        return self._chunks_read

    @property
    def total_bytes(self):
        return self._total_bytes

    @property
    def is_finished(self):
        return self._finished

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def __repr__(self):
        return (
            f"ChunkedReader(chunk_size={self.chunk_size}, "
            f"chunks_read={self._chunks_read})"
        )
