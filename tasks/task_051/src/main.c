#include <stdio.h>
#include "dynarray.h"

int main(int argc, char *argv[]) {
    DynArray arr;
    int val;
    int ret;

    if (argc < 2) {
        printf("Usage: %s <test_name>\n", argv[0]);
        return 1;
    }

    if (strcmp(argv[1], "basic_push_get") == 0) {
        dynarray_init(&arr);
        for (int i = 0; i < 10; i++) {
            ret = dynarray_push(&arr, i * 10);
            if (ret != 0) {
                printf("FAIL: push failed at index %d\n", i);
                dynarray_free(&arr);
                return 1;
            }
        }
        int ok = 1;
        for (int i = 0; i < 10; i++) {
            ret = dynarray_get(&arr, i, &val);
            if (ret != 0 || val != i * 10) {
                printf("FAIL: get(%d) returned %d, expected %d\n", i, val, i * 10);
                ok = 0;
            }
        }
        if (ok) {
            printf("PASS: basic_push_get\n");
        }
        dynarray_free(&arr);

    } else if (strcmp(argv[1], "bounds_check") == 0) {
        dynarray_init(&arr);
        dynarray_push(&arr, 42);
        dynarray_push(&arr, 84);
        /* Try to get at index 100 — should return error */
        ret = dynarray_get(&arr, 100, &val);
        if (ret == -1) {
            printf("PASS: bounds_check correctly rejected index 100\n");
        } else {
            printf("FAIL: bounds_check allowed out-of-bounds read at index 100\n");
        }
        dynarray_free(&arr);

    } else if (strcmp(argv[1], "grow_large") == 0) {
        dynarray_init(&arr);
        int ok = 1;
        for (int i = 0; i < 1000; i++) {
            ret = dynarray_push(&arr, i);
            if (ret != 0) {
                printf("FAIL: push failed at %d\n", i);
                ok = 0;
                break;
            }
        }
        if (ok) {
            for (int i = 0; i < 1000; i++) {
                ret = dynarray_get(&arr, i, &val);
                if (ret != 0 || val != i) {
                    printf("FAIL: get(%d) = %d, expected %d\n", i, val, i);
                    ok = 0;
                    break;
                }
            }
        }
        if (ok) {
            printf("PASS: grow_large\n");
        }
        dynarray_free(&arr);

    } else {
        printf("Unknown test: %s\n", argv[1]);
        return 1;
    }

    return 0;
}
