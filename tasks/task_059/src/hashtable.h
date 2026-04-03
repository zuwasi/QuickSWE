#ifndef HASHTABLE_H
#define HASHTABLE_H

#include <stdlib.h>

typedef struct Entry {
    int key;
    int value;
    struct Entry *next;
} Entry;

typedef struct {
    Entry **buckets;
    int capacity;
    int size;
} HashTable;

HashTable *ht_create(int capacity);
void ht_insert(HashTable *ht, int key, int value);
int ht_get(HashTable *ht, int key, int *out_value);
int ht_remove(HashTable *ht, int key);
void ht_free(HashTable *ht);

#endif
