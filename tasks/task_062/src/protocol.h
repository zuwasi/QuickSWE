#ifndef PROTOCOL_H
#define PROTOCOL_H

#include <stdint.h>
#include <stddef.h>

#define MAX_STRING_LEN 256
#define MAX_BUFFER_SIZE 1024

typedef struct {
    uint32_t msg_type;
    uint32_t flags;
    /* TODO: add char sender[MAX_STRING_LEN] and char payload[MAX_STRING_LEN] */
    /* TODO: add uint32_t checksum */
} Message;

/*
 * Pack a Message into a byte buffer.
 * Returns the number of bytes written, or -1 on error.
 */
int msg_pack(const Message *msg, uint8_t *buf, size_t buf_size);

/*
 * Unpack a byte buffer into a Message.
 * Returns 0 on success, -1 on error (e.g., checksum mismatch).
 */
int msg_unpack(const uint8_t *buf, size_t buf_len, Message *msg);

#endif
