"""
Line splitter for splitting decoded text into lines.
Handles different line ending styles.
"""


class LineSplitter:
    """Splits decoded text into individual lines.

    Handles \\n, \\r\\n, and \\r line endings.
    """

    def __init__(self, keep_ends=False):
        """Initialize the line splitter.

        Args:
            keep_ends: If True, keep line ending characters in the output.
        """
        self.keep_ends = keep_ends
        self._total_lines = 0

    def split(self, text):
        """Split text into lines.

        Args:
            text: Decoded text string.

        Returns:
            List of line strings.
        """
        if not text:
            return []

        if self.keep_ends:
            lines = text.splitlines(True)
        else:
            lines = text.splitlines()

        self._total_lines += len(lines)
        return lines

    def split_stream(self, reader, decoder):
        """Split a chunked byte stream into lines.

        Reads chunks, decodes them, and splits into lines.
        Handles lines that span chunk boundaries.

        NOTE: This method correctly handles LINE boundaries across chunks,
        but the decoder bug (not handling character boundaries) happens
        BEFORE this method gets the text.
        """
        all_lines = []
        buffer = ""

        while True:
            chunk = reader.read_chunk()
            if chunk is None:
                break

            text = decoder.decode_chunk(chunk)
            buffer += text

            # Split complete lines
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if not self.keep_ends:
                    line = line.rstrip("\r")
                else:
                    line = line + "\n"
                all_lines.append(line)

        # Handle remaining buffer (last line without newline)
        if buffer:
            if not self.keep_ends:
                buffer = buffer.rstrip("\r")
            all_lines.append(buffer)

        self._total_lines = len(all_lines)
        return all_lines

    @property
    def total_lines(self):
        return self._total_lines

    def reset(self):
        """Reset line count."""
        self._total_lines = 0

    def __repr__(self):
        return f"LineSplitter(keep_ends={self.keep_ends}, lines={self._total_lines})"


def process_text_file(source, chunk_size=4096, keep_line_ends=False):
    """Convenience function to read and split a text file into lines.

    Args:
        source: File path, bytes, or file-like object.
        chunk_size: Chunk size for reading.
        keep_line_ends: Whether to preserve line endings.

    Returns:
        List of lines.
    """
    from .chunked_reader import ChunkedReader
    from .decoder import Decoder

    reader = ChunkedReader(source, chunk_size=chunk_size)
    decoder = Decoder()
    splitter = LineSplitter(keep_ends=keep_line_ends)

    try:
        return splitter.split_stream(reader, decoder)
    finally:
        reader.close()
