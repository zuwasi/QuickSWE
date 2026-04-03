#include "dynarray.h"
#include <string.h>

int dynarray_init(DynArray *arr) {
    arr->data = NULL;
    arr->size = 0;
    arr->capacity = 0;
    return 0;
}

int dynarray_push(DynArray *arr, int value) {
    if (arr->size >= arr->capacity) {
        /* BUG: when capacity is 0, new_capacity becomes 0 * 2 = 0.
           realloc(NULL, 0) returns NULL or a minimal block,
           so data stays NULL or is a zero-size allocation. */
        size_t new_capacity = arr->capacity * 2;
        int *new_data = (int *)realloc(arr->data, new_capacity * sizeof(int));
        if (new_data == NULL) {
            return -1;
        }
        arr->data = new_data;
        arr->capacity = new_capacity;
    }
    arr->data[arr->size] = value;
    arr->size++;
    return 0;
}

int dynarray_get(DynArray *arr, size_t index, int *out) {
    /* BUG: no bounds checking — reads beyond size are silently allowed */
    *out = arr->data[index];
    return 0;
}

void dynarray_free(DynArray *arr) {
    free(arr->data);
    arr->data = NULL;
    arr->size = 0;
    arr->capacity = 0;
}
