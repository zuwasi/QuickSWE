"""
Decoder module for converting byte chunks to text.
Handles UTF-8 decoding of byte streams.
"""


class DecodeError(Exception):
    """Raised when decoding fails."""
    pass


class Decoder:
    """Decodes byte chunks into text strings.

    BUG: Each chunk is decoded independently. If a multi-byte UTF-8
    character spans a chunk boundary, the partial bytes at the end of
    one chunk and beginning of the next will cause decode errors or
    produce replacement characters.
    """

    def __init__(self, encoding="utf-8", errors="strict"):
        """Initialize the decoder.

        Args:
            encoding: Text encoding to use.
            errors: Error handling mode ('strict', 'replace', 'ignore').
        """
        self.encoding = encoding
        self.errors = errors
        self._chunks_decoded = 0
        self._decode_errors = 0
        # Red herring: buffer exists but is never populated
        self._leftover_buffer = b""

    def decode_chunk(self, chunk):
        """Decode a single byte chunk to text.

        BUG: Decodes each chunk independently without handling partial
        multi-byte characters at chunk boundaries.
        """
        if not chunk:
            return ""

        try:
            # BUG: This will fail if chunk ends in the middle of a
            # multi-byte UTF-8 sequence (e.g., half of an emoji)
            text = chunk.decode(self.encoding, errors=self.errors)
            self._chunks_decoded += 1
            return text
        except UnicodeDecodeError as e:
            self._decode_errors += 1
            raise DecodeError(
                f"Failed to decode chunk: {e}"
            ) from e

    def decode_chunks(self, chunks):
        """Decode a sequence of byte chunks to text.

        BUG: Calls decode_chunk on each chunk independently —
        does not carry over partial characters between chunks.
        """
        parts = []
        for chunk in chunks:
            parts.append(self.decode_chunk(chunk))
        return "".join(parts)

    def decode_stream(self, reader):
        """Decode all chunks from a ChunkedReader.

        Args:
            reader: A ChunkedReader instance.

        Returns:
            The fully decoded text.
        """
        parts = []
        while True:
            chunk = reader.read_chunk()
            if chunk is None:
                break
            parts.append(self.decode_chunk(chunk))

        # Red herring: flush leftover (but it's always empty)
        if self._leftover_buffer:
            parts.append(
                self._leftover_buffer.decode(self.encoding, errors=self.errors)
            )
            self._leftover_buffer = b""

        return "".join(parts)

    @property
    def stats(self):
        return {
            "chunks_decoded": self._chunks_decoded,
            "decode_errors": self._decode_errors,
        }

    def reset(self):
        """Reset decoder state."""
        self._chunks_decoded = 0
        self._decode_errors = 0
        self._leftover_buffer = b""

    def __repr__(self):
        return (
            f"Decoder(encoding={self.encoding!r}, "
            f"decoded={self._chunks_decoded}, "
            f"errors={self._decode_errors})"
        )
