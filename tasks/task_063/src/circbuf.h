#ifndef CIRCBUF_H
#define CIRCBUF_H

#define CB_CAPACITY 4

typedef struct {
    int data[CB_CAPACITY];
    int read_pos;
    int write_pos;
} CircBuf;

void cb_init(CircBuf *cb);
int  cb_write(CircBuf *cb, int value);   /* returns 0 on success, -1 if full */
int  cb_read(CircBuf *cb, int *out);     /* returns 0 on success, -1 if empty */
int  cb_count(CircBuf *cb);              /* number of unread items */
int  cb_is_empty(CircBuf *cb);
int  cb_is_full(CircBuf *cb);

#endif
