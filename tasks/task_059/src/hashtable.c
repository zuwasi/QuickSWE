#include "hashtable.h"
#include <stdio.h>
#include <string.h>

static int hash(int key, int capacity) {
    /* BUG: does not handle negative keys — key % capacity can be negative in C */
    return key % capacity;
}

HashTable *ht_create(int capacity) {
    HashTable *ht = (HashTable *)malloc(sizeof(HashTable));
    ht->capacity = capacity;
    ht->size = 0;
    ht->buckets = (Entry **)calloc(capacity, sizeof(Entry *));
    return ht;
}

static void ht_resize(HashTable *ht) {
    int old_cap = ht->capacity;
    int new_cap = old_cap * 2;
    Entry **new_buckets = (Entry **)calloc(new_cap, sizeof(Entry *));

    /* BUG: just copies bucket pointers instead of rehashing each entry */
    for (int i = 0; i < old_cap; i++) {
        new_buckets[i] = ht->buckets[i];
    }

    free(ht->buckets);
    ht->buckets = new_buckets;
    ht->capacity = new_cap;
}

void ht_insert(HashTable *ht, int key, int value) {
    if ((float)ht->size / ht->capacity > 0.75f) {
        ht_resize(ht);
    }

    int idx = hash(key, ht->capacity);
    /* Check if key already exists */
    Entry *cur = ht->buckets[idx];
    while (cur) {
        if (cur->key == key) {
            cur->value = value;
            return;
        }
        cur = cur->next;
    }

    Entry *e = (Entry *)malloc(sizeof(Entry));
    e->key = key;
    e->value = value;
    e->next = ht->buckets[idx];
    ht->buckets[idx] = e;
    ht->size++;
}

int ht_get(HashTable *ht, int key, int *out_value) {
    int idx = hash(key, ht->capacity);
    Entry *cur = ht->buckets[idx];
    while (cur) {
        if (cur->key == key) {
            *out_value = cur->value;
            return 1;
        }
        cur = cur->next;
    }
    return 0;
}

int ht_remove(HashTable *ht, int key) {
    int idx = hash(key, ht->capacity);
    Entry *cur = ht->buckets[idx];
    Entry *prev = NULL;
    while (cur) {
        if (cur->key == key) {
            if (prev) prev->next = cur->next;
            else ht->buckets[idx] = cur->next;
            free(cur);
            ht->size--;
            return 1;
        }
        prev = cur;
        cur = cur->next;
    }
    return 0;
}

void ht_free(HashTable *ht) {
    for (int i = 0; i < ht->capacity; i++) {
        Entry *cur = ht->buckets[i];
        while (cur) {
            Entry *tmp = cur;
            cur = cur->next;
            free(tmp);
        }
    }
    free(ht->buckets);
    free(ht);
}
