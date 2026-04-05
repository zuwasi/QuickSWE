import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.varint import (
    encode_varint, decode_varint,
    encode_signed_varint, decode_signed_varint,
    VarintBuffer, varint_size,
)


class TestVarintPassToPass:
    """Tests that should pass both before and after the fix."""

    def test_encode_decode_zero(self):
        encoded = encode_varint(0)
        val, consumed = decode_varint(encoded)
        assert val == 0

    def test_encode_decode_small(self):
        for v in [1, 127, 128, 255, 300]:
            encoded = encode_varint(v)
            decoded, _ = decode_varint(encoded)
            assert decoded == v

    def test_signed_varint_small(self):
        for v in [-1, 0, 1, -100, 100]:
            encoded = encode_signed_varint(v)
            decoded, _ = decode_signed_varint(encoded)
            assert decoded == v

    def test_varint_buffer_string(self):
        buf = VarintBuffer()
        buf.write_string("hello")
        buf.reset_read()
        assert buf.read_string() == "hello"


@pytest.mark.fail_to_pass
class TestVarintFailToPass:
    """Tests that fail before the fix and pass after."""

    def test_encode_decode_large_32bit(self):
        value = 2**31 - 1
        encoded = encode_varint(value)
        decoded, _ = decode_varint(encoded)
        assert decoded == value

    def test_encode_decode_2_pow_32(self):
        value = 2**32
        encoded = encode_varint(value)
        decoded, _ = decode_varint(encoded)
        assert decoded == value

    def test_encode_decode_64bit(self):
        value = 2**63 - 1
        encoded = encode_varint(value)
        decoded, _ = decode_varint(encoded)
        assert decoded == value
