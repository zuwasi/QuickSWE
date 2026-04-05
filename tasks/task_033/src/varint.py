"""
Protocol Buffer-style varint encoding and decoding.

Encodes unsigned integers using 7 bits per byte with the MSB as a
continuation flag. Supports message framing with length-prefixed messages.
"""

from typing import List, Tuple, Optional, BinaryIO
import struct
import io


def encode_varint(value: int) -> bytes:
    """Encode an unsigned integer as a varint.

    Each byte uses 7 bits for data and 1 bit (MSB) as continuation flag.
    """
    if value < 0:
        raise ValueError("Varint encoding requires non-negative integers")

    if value == 0:
        return b'\x00'

    result = bytearray()
    remaining = value
    iterations = 0

    while remaining > 0 and iterations < 4:
        byte = remaining & 0x7F
        remaining >>= 7
        if remaining > 0:
            byte |= 0x80
        result.append(byte)
        iterations += 1

    return bytes(result)


def decode_varint(data: bytes, offset: int = 0) -> Tuple[int, int]:
    """Decode a varint from bytes at the given offset.

    Returns (value, bytes_consumed).
    """
    result = 0
    shift = 0
    bytes_consumed = 0

    for i in range(offset, len(data)):
        byte = data[i]
        result |= (byte & 0x7F) << shift
        shift += 7
        bytes_consumed += 1
        if not (byte & 0x80):
            break

    return result, bytes_consumed


def encode_signed_varint(value: int) -> bytes:
    """Encode a signed integer using ZigZag encoding then varint."""
    if value >= 0:
        zigzag = value * 2
    else:
        zigzag = (-value) * 2 - 1
    return encode_varint(zigzag)


def decode_signed_varint(data: bytes, offset: int = 0) -> Tuple[int, int]:
    """Decode a ZigZag-encoded signed varint."""
    zigzag, consumed = decode_varint(data, offset)
    if zigzag & 1:
        value = -((zigzag + 1) // 2)
    else:
        value = zigzag // 2
    return value, consumed


class VarintBuffer:
    """Buffer for reading/writing varint-encoded values."""

    def __init__(self, data: bytes = b''):
        self._buffer = bytearray(data)
        self._read_pos = 0

    def write_varint(self, value: int):
        self._buffer.extend(encode_varint(value))

    def write_signed(self, value: int):
        self._buffer.extend(encode_signed_varint(value))

    def write_bytes(self, data: bytes):
        self.write_varint(len(data))
        self._buffer.extend(data)

    def write_string(self, text: str):
        encoded = text.encode('utf-8')
        self.write_bytes(encoded)

    def read_varint(self) -> int:
        if self._read_pos >= len(self._buffer):
            raise EOFError("No more data to read")
        value, consumed = decode_varint(bytes(self._buffer), self._read_pos)
        self._read_pos += consumed
        return value

    def read_signed(self) -> int:
        if self._read_pos >= len(self._buffer):
            raise EOFError("No more data to read")
        value, consumed = decode_signed_varint(bytes(self._buffer), self._read_pos)
        self._read_pos += consumed
        return value

    def read_bytes(self) -> bytes:
        length = self.read_varint()
        data = bytes(self._buffer[self._read_pos:self._read_pos + length])
        self._read_pos += length
        return data

    def read_string(self) -> str:
        return self.read_bytes().decode('utf-8')

    def get_data(self) -> bytes:
        return bytes(self._buffer)

    def remaining(self) -> int:
        return len(self._buffer) - self._read_pos

    def reset_read(self):
        self._read_pos = 0


class MessageFramer:
    """Frames messages with length-prefixed varint encoding."""

    @staticmethod
    def frame_message(payload: bytes) -> bytes:
        length_prefix = encode_varint(len(payload))
        return length_prefix + payload

    @staticmethod
    def unframe_messages(data: bytes) -> List[bytes]:
        messages = []
        offset = 0
        while offset < len(data):
            length, consumed = decode_varint(data, offset)
            offset += consumed
            payload = data[offset:offset + length]
            messages.append(payload)
            offset += length
        return messages


def varint_size(value: int) -> int:
    """Return the number of bytes needed to encode a value as varint."""
    if value == 0:
        return 1
    size = 0
    while value > 0:
        size += 1
        value >>= 7
    return size
