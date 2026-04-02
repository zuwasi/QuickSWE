"""Tests for the chunked text reader pipeline."""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.chunked_reader import ChunkedReader
from src.decoder import Decoder, DecodeError
from src.line_splitter import LineSplitter, process_text_file


# ── pass-to-pass: these must always pass ─────────────────────────────────

class TestAsciiOnlyText:
    """Pure ASCII text works fine regardless of chunk boundaries."""

    def test_ascii_only_text(self):
        text = "Hello, World!\nThis is a test.\nLine three.\n"
        data = text.encode("utf-8")

        # Small chunks — ASCII never has multi-byte chars
        reader = ChunkedReader(data, chunk_size=10)
        decoder = Decoder()
        result = decoder.decode_stream(reader)
        reader.close()

        assert result == text
        assert reader.chunks_read > 1  # Verify multiple chunks


class TestLineSplitterBasic:
    """Line splitter works on pre-decoded text."""

    def test_line_splitter_basic(self):
        splitter = LineSplitter()

        lines = splitter.split("one\ntwo\nthree")
        assert lines == ["one", "two", "three"]

        lines_crlf = splitter.split("a\r\nb\r\nc")
        assert lines_crlf == ["a", "b", "c"]

        assert splitter.split("") == []

        # With line ends
        splitter2 = LineSplitter(keep_ends=True)
        lines_ke = splitter2.split("x\ny\n")
        assert lines_ke == ["x\n", "y\n"]


class TestDecoderSimpleUtf8:
    """Decoder works when given complete UTF-8 sequences."""

    def test_decoder_simple_utf8(self):
        decoder = Decoder()

        # Single chunk with complete characters
        text = "Héllo Wörld café"
        chunk = text.encode("utf-8")
        assert decoder.decode_chunk(chunk) == text

        # Emoji in a single chunk
        emoji_text = "Hello 🌍🎉"
        emoji_chunk = emoji_text.encode("utf-8")
        assert decoder.decode_chunk(emoji_chunk) == emoji_text


# ── fail-to-pass: these FAIL with the bug, PASS after fix ────────────────

class TestMultibyteAtBoundary:
    """Multi-byte characters split across chunk boundaries."""

    @pytest.mark.fail_to_pass
    def test_multibyte_char_at_chunk_boundary(self):
        """A 2-byte UTF-8 character (e.g., 'é' = 0xC3 0xA9) is split
        across two chunks. The decoder must handle this correctly.
        """
        # Build text where a multi-byte char falls exactly at chunk boundary
        # 'é' is 2 bytes in UTF-8: \\xc3\\xa9
        # Place it so the first byte is at the end of chunk 1
        text = "A" * 7 + "é" + "B" * 7  # 7 ASCII + 2-byte char + 7 ASCII
        data = text.encode("utf-8")  # 7 + 2 + 7 = 16 bytes

        # Chunk size = 8: first chunk = 7 A's + first byte of é
        # Second chunk = second byte of é + 7 B's
        result = process_text_file(data, chunk_size=8)

        # Should produce one line with the full text
        full_result = "\n".join(result) if len(result) > 1 else result[0]
        assert "é" in full_result, (
            f"Multi-byte character lost at chunk boundary: {full_result!r}"
        )
        assert full_result == text


class TestEmojiAcrossBoundaries:
    """Emoji characters (4 bytes) split across chunk boundaries."""

    @pytest.mark.fail_to_pass
    def test_emoji_across_boundaries(self):
        """Emoji like 🌍 is 4 bytes (\\xf0\\x9f\\x8c\\x8d). When chunk size
        splits it, the decoder must reassemble correctly.
        """
        # 🌍 = 4 bytes. Place text so emoji spans boundary.
        text = "AB🌍CD"
        data = text.encode("utf-8")  # 2 + 4 + 2 = 8 bytes

        # Chunk size = 3: chunk1 = "AB" + first byte of 🌍
        # chunk2 = bytes 2-4 of 🌍 (3 bytes)
        # chunk3 = "CD"
        result = process_text_file(data, chunk_size=3)
        full_result = "".join(result)

        assert "🌍" in full_result, (
            f"Emoji lost at chunk boundary: {full_result!r}"
        )
        assert full_result == text


class TestCjkWithSmallChunks:
    """CJK text with small chunk sizes triggers many boundary splits."""

    @pytest.mark.fail_to_pass
    def test_cjk_text_with_small_chunks(self):
        """CJK characters are 3 bytes each. With chunk_size=4, every
        second character may span a boundary.
        """
        text = "你好世界测试文本"  # 8 CJK chars, 3 bytes each = 24 bytes
        data = text.encode("utf-8")
        assert len(data) == 24

        # chunk_size=4: chunks will split CJK chars
        # chunk1: bytes 0-3 (first char + 1 byte of second)
        # chunk2: bytes 4-7 (2 bytes of second char + 2 bytes of third)
        # etc.
        result = process_text_file(data, chunk_size=4)
        full_result = "".join(result)

        assert full_result == text, (
            f"CJK text corrupted with small chunks: "
            f"got {full_result!r}, expected {text!r}"
        )
