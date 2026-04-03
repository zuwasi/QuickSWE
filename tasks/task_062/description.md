# Feature: Add Serialization to Binary Protocol

## Description

A simple binary message protocol has `pack` and `unpack` functions for a `Message` struct containing fixed-size integer fields. Two features need to be added:

1. **Variable-length string fields**: Currently only fixed-size `uint32_t` fields are supported. Add support for a `sender` string and a `payload` string in the `Message` struct. Strings should be packed as: `[uint16_t length][bytes...]` (length-prefixed). The `msg_pack` function must serialize these, and `msg_unpack` must deserialize them.

2. **Checksum validation**: Add a `checksum` field (uint32_t) that is computed over all preceding packed bytes using a simple sum-of-bytes algorithm. `msg_pack` appends the checksum at the end of the buffer. `msg_unpack` verifies the checksum and returns an error code if it doesn't match (indicating corruption).

## Expected Behavior

- `msg_pack` serializes: `[msg_type(u32)][flags(u32)][sender_len(u16)][sender_bytes...][payload_len(u16)][payload_bytes...][checksum(u32)]`
- `msg_unpack` deserializes and validates the checksum, returning -1 on mismatch.
- Round-trip: pack then unpack should yield identical struct contents.

## Files

- `src/protocol.h` — Message struct and function declarations
- `src/protocol.c` — pack/unpack implementation (currently fixed-size only)
- `src/main.c` — test driver
