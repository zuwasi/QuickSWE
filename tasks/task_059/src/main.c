#include <stdio.h>
#include "hashtable.h"

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Usage: prog <test_name>\n");
        return 1;
    }

    const char *test = argv[1];

    if (strcmp(test, "basic_insert_get") == 0) {
        HashTable *ht = ht_create(8);
        ht_insert(ht, 1, 10);
        ht_insert(ht, 2, 20);
        ht_insert(ht, 3, 30);
        int val;
        if (ht_get(ht, 1, &val)) printf("1=%d\n", val);
        if (ht_get(ht, 2, &val)) printf("2=%d\n", val);
        if (ht_get(ht, 3, &val)) printf("3=%d\n", val);
        ht_free(ht);
    }
    else if (strcmp(test, "negative_keys") == 0) {
        HashTable *ht = ht_create(8);
        ht_insert(ht, -5, 500);
        ht_insert(ht, -10, 1000);
        ht_insert(ht, -1, 100);
        int val;
        int f1 = ht_get(ht, -5, &val);
        if (f1) printf("-5=%d\n", val); else printf("-5=NOT_FOUND\n");
        int f2 = ht_get(ht, -10, &val);
        if (f2) printf("-10=%d\n", val); else printf("-10=NOT_FOUND\n");
        int f3 = ht_get(ht, -1, &val);
        if (f3) printf("-1=%d\n", val); else printf("-1=NOT_FOUND\n");
        ht_free(ht);
    }
    else if (strcmp(test, "resize_rehash") == 0) {
        HashTable *ht = ht_create(4);
        /* Insert enough to trigger resize (load > 0.75 means > 3 items for cap=4) */
        for (int i = 0; i < 20; i++) {
            ht_insert(ht, i * 7, i * 100);
        }
        /* Now verify all entries are still findable */
        int all_found = 1;
        int val;
        for (int i = 0; i < 20; i++) {
            if (!ht_get(ht, i * 7, &val) || val != i * 100) {
                all_found = 0;
                printf("MISSING key=%d\n", i * 7);
            }
        }
        if (all_found) printf("ALL_FOUND\n");
        ht_free(ht);
    }
    else if (strcmp(test, "update_value") == 0) {
        HashTable *ht = ht_create(8);
        ht_insert(ht, 42, 1);
        ht_insert(ht, 42, 2);
        int val;
        if (ht_get(ht, 42, &val)) printf("42=%d\n", val);
        ht_free(ht);
    }
    else if (strcmp(test, "remove") == 0) {
        HashTable *ht = ht_create(8);
        ht_insert(ht, 10, 100);
        ht_insert(ht, 20, 200);
        ht_remove(ht, 10);
        int val;
        int f1 = ht_get(ht, 10, &val);
        printf("10=%s\n", f1 ? "FOUND" : "NOT_FOUND");
        int f2 = ht_get(ht, 20, &val);
        if (f2) printf("20=%d\n", val);
        ht_free(ht);
    }
    else {
        printf("Unknown test: %s\n", test);
        return 1;
    }

    return 0;
}
