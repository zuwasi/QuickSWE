#include <stdio.h>
#include <string.h>
#include "protocol.h"

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Usage: prog <test_name>\n");
        return 1;
    }

    const char *test = argv[1];

    if (strcmp(test, "basic_fixed_fields") == 0) {
        /* Test that existing fixed fields still work */
        Message out, in;
        memset(&out, 0, sizeof(out));
        memset(&in, 0, sizeof(in));
        out.msg_type = 42;
        out.flags = 0xFF00;

        uint8_t buf[MAX_BUFFER_SIZE];
        int len = msg_pack(&out, buf, sizeof(buf));
        if (len < 0) { printf("PACK_ERROR\n"); return 1; }

        int rc = msg_unpack(buf, len, &in);
        if (rc != 0) { printf("UNPACK_ERROR\n"); return 1; }

        printf("msg_type=%u\n", in.msg_type);
        printf("flags=%u\n", in.flags);
    }
    else if (strcmp(test, "string_roundtrip") == 0) {
        /* Test variable-length string packing/unpacking */
        Message out, in;
        memset(&out, 0, sizeof(out));
        memset(&in, 0, sizeof(in));
        out.msg_type = 1;
        out.flags = 0;
#ifdef HAS_STRINGS
        strncpy(out.sender, "Alice", MAX_STRING_LEN - 1);
        strncpy(out.payload, "Hello, World!", MAX_STRING_LEN - 1);
#endif

        uint8_t buf[MAX_BUFFER_SIZE];
        int len = msg_pack(&out, buf, sizeof(buf));
        if (len < 0) { printf("PACK_ERROR\n"); return 1; }

        int rc = msg_unpack(buf, len, &in);
        if (rc != 0) { printf("UNPACK_ERROR\n"); return 1; }

        printf("msg_type=%u\n", in.msg_type);
#ifdef HAS_STRINGS
        printf("sender=%s\n", in.sender);
        printf("payload=%s\n", in.payload);
#else
        printf("sender=NOT_IMPLEMENTED\n");
        printf("payload=NOT_IMPLEMENTED\n");
#endif
    }
    else if (strcmp(test, "checksum_valid") == 0) {
        Message out, in;
        memset(&out, 0, sizeof(out));
        memset(&in, 0, sizeof(in));
        out.msg_type = 99;
        out.flags = 7;
#ifdef HAS_STRINGS
        strncpy(out.sender, "Bob", MAX_STRING_LEN - 1);
        strncpy(out.payload, "Test data", MAX_STRING_LEN - 1);
#endif

        uint8_t buf[MAX_BUFFER_SIZE];
        int len = msg_pack(&out, buf, sizeof(buf));
        if (len < 0) { printf("PACK_ERROR\n"); return 1; }

        /* The packed buffer should be larger than just fixed fields (8 bytes)
         * if strings and checksum are implemented */
        printf("packed_len=%d\n", len);

        int rc = msg_unpack(buf, len, &in);
        printf("unpack_rc=%d\n", rc);
        printf("msg_type=%u\n", in.msg_type);
    }
    else if (strcmp(test, "checksum_corrupt") == 0) {
        Message out, in;
        memset(&out, 0, sizeof(out));
        memset(&in, 0, sizeof(in));
        out.msg_type = 5;
        out.flags = 3;
#ifdef HAS_STRINGS
        strncpy(out.sender, "Eve", MAX_STRING_LEN - 1);
        strncpy(out.payload, "Tampered", MAX_STRING_LEN - 1);
#endif

        uint8_t buf[MAX_BUFFER_SIZE];
        int len = msg_pack(&out, buf, sizeof(buf));
        if (len < 0) { printf("PACK_ERROR\n"); return 1; }

        /* Corrupt a byte in the middle of the buffer */
        if (len > 5) buf[5] ^= 0xFF;

        int rc = msg_unpack(buf, len, &in);
        printf("unpack_rc=%d\n", rc);
    }
    else if (strcmp(test, "empty_strings") == 0) {
        Message out, in;
        memset(&out, 0, sizeof(out));
        memset(&in, 0, sizeof(in));
        out.msg_type = 10;
        out.flags = 0;
        /* sender and payload are empty strings (zeroed by memset) */

        uint8_t buf[MAX_BUFFER_SIZE];
        int len = msg_pack(&out, buf, sizeof(buf));
        if (len < 0) { printf("PACK_ERROR\n"); return 1; }

        int rc = msg_unpack(buf, len, &in);
        if (rc != 0) { printf("UNPACK_ERROR\n"); return 1; }

        printf("msg_type=%u\n", in.msg_type);
#ifdef HAS_STRINGS
        printf("sender_len=%d\n", (int)strlen(in.sender));
        printf("payload_len=%d\n", (int)strlen(in.payload));
#else
        printf("sender_len=NOT_IMPLEMENTED\n");
        printf("payload_len=NOT_IMPLEMENTED\n");
#endif
    }
    else {
        printf("Unknown test: %s\n", test);
        return 1;
    }

    return 0;
}
