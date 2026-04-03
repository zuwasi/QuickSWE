#ifndef LIST_H
#define LIST_H

#include <stdlib.h>

typedef struct ListNode {
    char *data;               /* dynamically allocated string (strdup) */
    struct ListNode *next;
} ListNode;

typedef struct {
    ListNode *head;
    size_t length;
} List;

/* Create a new empty list. Returns NULL on failure. */
List *list_create(void);

/* Insert a string at the head. Data is duplicated internally. Returns 0 on success. */
int list_insert(List *list, const char *data);

/* Delete first node matching data. Returns 0 if found and deleted, -1 if not found. */
int list_delete(List *list, const char *data);

/* Find a node by data. Returns pointer to node or NULL. */
ListNode *list_find(List *list, const char *data);

/* Destroy the entire list and all its nodes. */
void list_destroy(List *list);

/* Print all elements, one per line. */
void list_print(List *list);

#endif /* LIST_H */
