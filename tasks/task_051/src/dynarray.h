#ifndef DYNARRAY_H
#define DYNARRAY_H

#include <stdlib.h>

typedef struct {
    int *data;
    size_t size;
    size_t capacity;
} DynArray;

/* Initialize a dynamic array. Capacity starts at 0. */
int dynarray_init(DynArray *arr);

/* Push a value onto the end of the array. Returns 0 on success, -1 on error. */
int dynarray_push(DynArray *arr, int value);

/* Get value at index. Stores result in *out. Returns 0 on success, -1 on error. */
int dynarray_get(DynArray *arr, size_t index, int *out);

/* Free all memory used by the array. */
void dynarray_free(DynArray *arr);

#endif /* DYNARRAY_H */
