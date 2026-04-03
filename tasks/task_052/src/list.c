#include "list.h"
#include <stdio.h>
#include <string.h>

List *list_create(void) {
    List *list = (List *)malloc(sizeof(List));
    if (!list) return NULL;
    list->head = NULL;
    list->length = 0;
    return list;
}

int list_insert(List *list, const char *data) {
    if (!list || !data) return -1;

    ListNode *node = (ListNode *)malloc(sizeof(ListNode));
    if (!node) return -1;

    node->data = _strdup(data);  /* duplicate the string */
    if (!node->data) {
        free(node);
        return -1;
    }

    node->next = list->head;
    list->head = node;
    list->length++;
    return 0;
}

int list_delete(List *list, const char *data) {
    if (!list || !data || !list->head) return -1;

    ListNode *prev = NULL;
    ListNode *curr = list->head;

    while (curr) {
        if (strcmp(curr->data, data) == 0) {
            if (prev) {
                prev->next = curr->next;
            } else {
                list->head = curr->next;
            }
            /* BUG: frees the node but NOT the strdup'd data pointer */
            free(curr);
            list->length--;
            return 0;
        }
        prev = curr;
        curr = curr->next;
    }
    return -1;
}

ListNode *list_find(List *list, const char *data) {
    if (!list || !data) return NULL;

    ListNode *curr = list->head;
    while (curr) {
        if (strcmp(curr->data, data) == 0) {
            return curr;
        }
        curr = curr->next;
    }
    return NULL;
}

void list_destroy(List *list) {
    if (!list) return;

    ListNode *curr = list->head;
    while (curr) {
        ListNode *next = curr->next;
        free(curr->data);
        free(curr);
        curr = next;
    }
    /* BUG: does NOT free the list struct itself */
}

void list_print(List *list) {
    if (!list) return;

    ListNode *curr = list->head;
    while (curr) {
        printf("%s\n", curr->data);
        curr = curr->next;
    }
}
