#include "circbuf.h"

void cb_init(CircBuf *cb) {
    cb->read_pos = 0;
    cb->write_pos = 0;
}

int cb_write(CircBuf *cb, int value) {
    int next = (cb->write_pos + 1) % CB_CAPACITY;
    if (next == cb->read_pos) {
        return -1;  /* full */
    }
    cb->data[cb->write_pos] = value;
    cb->write_pos = next;  /* correctly wraps */
    return 0;
}

int cb_read(CircBuf *cb, int *out) {
    /* BUG: simple comparison fails when write_pos has wrapped around */
    if (cb->read_pos >= cb->write_pos) {
        return -1;  /* thinks it's empty when write_pos < read_pos */
    }
    *out = cb->data[cb->read_pos];
    cb->read_pos = (cb->read_pos + 1) % CB_CAPACITY;
    return 0;
}

int cb_count(CircBuf *cb) {
    /* BUG: doesn't handle wrap — returns negative when write_pos < read_pos */
    return cb->write_pos - cb->read_pos;
}

int cb_is_empty(CircBuf *cb) {
    return cb_count(cb) == 0;
}

int cb_is_full(CircBuf *cb) {
    return cb_count(cb) == CB_CAPACITY - 1;
}
