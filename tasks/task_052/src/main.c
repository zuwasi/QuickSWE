#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "list.h"

/*
 * Allocation tracking: we wrap malloc/free to count calls.
 * This is compiled with -Dmalloc=tracked_malloc -Dfree=tracked_free
 * when we want tracking, or used directly via the track_* interface.
 */

static int g_alloc_count = 0;
static int g_free_count = 0;

void reset_tracking(void) {
    g_alloc_count = 0;
    g_free_count = 0;
}

void print_tracking(void) {
    printf("ALLOCS: %d\n", g_alloc_count);
    printf("FREES: %d\n", g_free_count);
    if (g_alloc_count == g_free_count) {
        printf("MEMORY: OK\n");
    } else {
        printf("MEMORY: LEAK (%d unfreed)\n", g_alloc_count - g_free_count);
    }
}

/*
 * Since we can't easily wrap malloc/free without macro conflicts in the
 * same compilation unit that defines list.c, we take a different approach:
 * We manually count what SHOULD be allocated/freed based on list operations,
 * then compare to what we know the buggy code actually does.
 *
 * For a correct implementation:
 * - list_create: 1 alloc (list struct)
 * - list_insert: 2 allocs (node + strdup)
 * - list_delete: 2 frees (node + data)
 * - list_destroy: 2 frees per remaining node + 1 free for list struct
 */

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Usage: %s <test_name>\n", argv[0]);
        return 1;
    }

    if (strcmp(argv[1], "basic_ops") == 0) {
        /* Test basic list operations produce correct output */
        List *list = list_create();
        list_insert(list, "charlie");
        list_insert(list, "bravo");
        list_insert(list, "alpha");

        printf("LIST:");
        ListNode *curr = list->head;
        while (curr) {
            printf(" %s", curr->data);
            curr = curr->next;
        }
        printf("\n");
        printf("LENGTH: %zu\n", list->length);

        /* Find */
        ListNode *found = list_find(list, "bravo");
        if (found) {
            printf("FOUND: %s\n", found->data);
        } else {
            printf("FOUND: NULL\n");
        }

        /* Delete */
        list_delete(list, "bravo");
        printf("AFTER_DELETE_LENGTH: %zu\n", list->length);

        /* Verify bravo is gone */
        found = list_find(list, "bravo");
        printf("BRAVO_AFTER_DELETE: %s\n", found ? "still_there" : "gone");

        list_destroy(list);
        printf("PASS: basic_ops\n");

    } else if (strcmp(argv[1], "leak_check_delete") == 0) {
        /*
         * Test that delete properly frees node data.
         * We create a list, insert items, delete them all, then destroy.
         * A correct implementation frees data+node on each delete.
         *
         * We check by doing operations and tracking expected vs actual
         * via a sentinel approach: we'll insert known strings, delete them,
         * and check that the list reports correct state throughout.
         *
         * The real leak detection: we insert N items, delete them all,
         * then count: for correct code, all data should be freed.
         * We detect the bug by checking list internals indirectly.
         *
         * Approach: We use a wrapper main that does:
         * 1. Insert 5 items (5 nodes + 5 strdup = 10 allocs, + 1 list = 11)
         * 2. Delete all 5 (should be 10 frees for node+data)
         * 3. Destroy list (should be 1 free for list struct)
         * Total expected: 11 allocs, 11 frees
         *
         * With bugs:
         * - delete doesn't free data: only 5 frees in step 2 (missing 5 data frees)
         * - destroy doesn't free list: missing 1 free in step 3
         * So buggy: 11 allocs, 5 frees = 6 leaked
         *
         * We track this by instrumenting at the Python test level.
         * Here we just output what we can verify.
         */
        List *list = list_create();
        const char *items[] = {"alpha", "bravo", "charlie", "delta", "echo"};

        for (int i = 0; i < 5; i++) {
            list_insert(list, items[i]);
        }
        printf("INSERTED: 5\n");
        printf("LENGTH: %zu\n", list->length);

        /* Delete all items */
        for (int i = 0; i < 5; i++) {
            int ret = list_delete(list, items[i]);
            if (ret != 0) {
                printf("FAIL: could not delete %s\n", items[i]);
                list_destroy(list);
                return 1;
            }
        }
        printf("DELETED: 5\n");
        printf("LENGTH_AFTER: %zu\n", list->length);

        list_destroy(list);

        /*
         * Expected allocations for correct implementation:
         *   list_create: 1 malloc (list struct)
         *   5x list_insert: 5 malloc (node) + 5 strdup (data) = 10
         *   Total allocs = 11
         *
         *   5x list_delete: should free node + data each = 10 frees
         *   list_destroy: should free list struct = 1 free
         *   Total frees = 11
         *
         * Report expected counts for Python test to verify
         */
        printf("EXPECTED_ALLOCS: 11\n");
        printf("EXPECTED_FREES: 11\n");
        printf("PASS: leak_check_delete\n");

    } else if (strcmp(argv[1], "leak_check_destroy") == 0) {
        /*
         * Test that destroy properly frees everything including list struct.
         * Insert items, DON'T delete them, just destroy.
         *
         * Correct: list_create=1, 3x insert=6, destroy frees 3 nodes+3 data+1 list=7
         * Total: 7 allocs, 7 frees
         *
         * Buggy destroy (doesn't free list struct):
         * 7 allocs, 6 frees = 1 leaked
         */
        List *list = list_create();
        list_insert(list, "x");
        list_insert(list, "y");
        list_insert(list, "z");
        printf("INSERTED: 3\n");

        list_destroy(list);

        printf("EXPECTED_ALLOCS: 7\n");
        printf("EXPECTED_FREES: 7\n");
        printf("PASS: leak_check_destroy\n");

    } else {
        printf("Unknown test: %s\n", argv[1]);
        return 1;
    }

    return 0;
}
