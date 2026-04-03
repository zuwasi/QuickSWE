#include <stdio.h>
#include <string.h>
#include "circbuf.h"

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Usage: prog <test_name>\n");
        return 1;
    }

    const char *test = argv[1];

    if (strcmp(test, "basic_write_read") == 0) {
        CircBuf cb;
        cb_init(&cb);
        cb_write(&cb, 10);
        cb_write(&cb, 20);
        int val;
        if (cb_read(&cb, &val) == 0) printf("%d\n", val);
        if (cb_read(&cb, &val) == 0) printf("%d\n", val);
        printf("empty=%d\n", cb_is_empty(&cb));
    }
    else if (strcmp(test, "wrap_around") == 0) {
        /*
         * Capacity=4, so we can hold 3 items (one slot wasted for full detection).
         * Write 3, read 2, write 2 more — this forces write_pos to wrap.
         */
        CircBuf cb;
        cb_init(&cb);

        /* Fill: write 3 items (positions 0,1,2) */
        cb_write(&cb, 100);
        cb_write(&cb, 200);
        cb_write(&cb, 300);

        /* Read 2 items — read_pos advances to 2 */
        int val;
        cb_read(&cb, &val); printf("r1=%d\n", val);  /* 100 */
        cb_read(&cb, &val); printf("r2=%d\n", val);  /* 200 */

        /* Write 2 more — write_pos wraps: 3 -> 0 -> 1 */
        cb_write(&cb, 400);
        cb_write(&cb, 500);

        /* Now read_pos=2, write_pos=1 (wrapped). Count should be 3. */
        printf("count=%d\n", cb_count(&cb));

        /* Should read: 300, 400, 500 */
        if (cb_read(&cb, &val) == 0) printf("r3=%d\n", val); else printf("r3=FAIL\n");
        if (cb_read(&cb, &val) == 0) printf("r4=%d\n", val); else printf("r4=FAIL\n");
        if (cb_read(&cb, &val) == 0) printf("r5=%d\n", val); else printf("r5=FAIL\n");

        printf("empty=%d\n", cb_is_empty(&cb));
    }
    else if (strcmp(test, "full_check") == 0) {
        CircBuf cb;
        cb_init(&cb);
        cb_write(&cb, 1);
        cb_write(&cb, 2);
        cb_write(&cb, 3);
        int rc = cb_write(&cb, 4);  /* should fail — full */
        printf("write_full_rc=%d\n", rc);
        printf("full=%d\n", cb_is_full(&cb));
    }
    else if (strcmp(test, "count_after_wrap") == 0) {
        CircBuf cb;
        cb_init(&cb);
        cb_write(&cb, 10);
        cb_write(&cb, 20);
        cb_write(&cb, 30);

        int val;
        cb_read(&cb, &val);  /* read 10, read_pos=1 */
        cb_read(&cb, &val);  /* read 20, read_pos=2 */
        cb_read(&cb, &val);  /* read 30, read_pos=3 */

        cb_write(&cb, 40);   /* write_pos goes 3->0 */
        printf("count=%d\n", cb_count(&cb));  /* should be 1 */

        if (cb_read(&cb, &val) == 0) printf("val=%d\n", val); else printf("val=FAIL\n");
    }
    else {
        printf("Unknown test: %s\n", test);
        return 1;
    }

    return 0;
}
