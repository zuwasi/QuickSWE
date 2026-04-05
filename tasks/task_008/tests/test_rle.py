import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.rle import encode, decode


# ──────────────────────────────────────────────
# pass_to_pass: these must always pass
# ──────────────────────────────────────────────


class TestRLEEncoder:
    """Tests for the encoder which works correctly."""

    def test_encode_basic(self):
        assert encode("aaabbc") == "3a2b1c"

    def test_encode_single_chars(self):
        assert encode("abcd") == "1a1b1c1d"

    def test_encode_empty(self):
        assert encode("") == ""


# ──────────────────────────────────────────────
# fail_to_pass: these fail before the fix
# ──────────────────────────────────────────────


class TestRLEDecoder:
    """Tests for the decoder — drops the last group."""

    @pytest.mark.fail_to_pass
    def test_decode_basic(self):
        """Decode should produce the full original string."""
        assert decode("3a2b1c") == "aaabbc"

    @pytest.mark.fail_to_pass
    def test_roundtrip(self):
        """encode then decode should reproduce the original string."""
        original = "aaabbbccccdddddeee"
        assert decode(encode(original)) == original

    @pytest.mark.fail_to_pass
    def test_decode_single_char(self):
        """A single character group should decode correctly."""
        assert decode("1x") == "x"
        assert decode("5z") == "zzzzz"
