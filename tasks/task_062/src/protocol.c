#include <string.h>
#include <stdio.h>
#include "protocol.h"

static void write_u32(uint8_t *buf, uint32_t val) {
    buf[0] = (val >> 24) & 0xFF;
    buf[1] = (val >> 16) & 0xFF;
    buf[2] = (val >> 8)  & 0xFF;
    buf[3] = val & 0xFF;
}

static uint32_t read_u32(const uint8_t *buf) {
    return ((uint32_t)buf[0] << 24) |
           ((uint32_t)buf[1] << 16) |
           ((uint32_t)buf[2] << 8)  |
           (uint32_t)buf[3];
}

/* TODO: add write_u16 / read_u16 helpers for string length prefix */
/* TODO: add checksum computation function */

int msg_pack(const Message *msg, uint8_t *buf, size_t buf_size) {
    size_t offset = 0;

    if (buf_size < 8) return -1;  /* minimum for two u32 fields */

    write_u32(buf + offset, msg->msg_type);
    offset += 4;

    write_u32(buf + offset, msg->flags);
    offset += 4;

    /* TODO: pack sender string as [u16 len][bytes] */
    /* TODO: pack payload string as [u16 len][bytes] */
    /* TODO: compute and append checksum */

    return (int)offset;
}

int msg_unpack(const uint8_t *buf, size_t buf_len, Message *msg) {
    size_t offset = 0;

    if (buf_len < 8) return -1;

    msg->msg_type = read_u32(buf + offset);
    offset += 4;

    msg->flags = read_u32(buf + offset);
    offset += 4;

    /* TODO: unpack sender string */
    /* TODO: unpack payload string */
    /* TODO: verify checksum */

    return 0;
}
