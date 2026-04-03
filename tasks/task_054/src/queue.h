#ifndef QUEUE_H
#define QUEUE_H

#include <stdlib.h>

#define QUEUE_MAX_SIZE 256

typedef struct {
    int items[QUEUE_MAX_SIZE];
    int head;            /* index of next item to dequeue */
    int tail;            /* index of next free slot */
    int count;           /* number of items currently in queue */
    int capacity;

    /* Simulated synchronization state */
    int waiting_pop;     /* 1 if a consumer is waiting for signal */
    int signaled;        /* 1 if a producer has signaled */
} Queue;

/* Initialize queue with given capacity (max QUEUE_MAX_SIZE). */
void queue_init(Queue *q, int capacity);

/* Push an item. Returns 0 on success, -1 if full. */
int queue_push(Queue *q, int item);

/*
 * Pop an item. Returns 0 on success (item stored in *out), -1 if empty.
 * 
 * When the queue is empty:
 * - Sets waiting_pop = 1 and returns -2 (WAITING)
 * - Caller should call queue_resume_pop() after a signal to complete the pop.
 *
 * BUG: Uses 'if' check instead of 'while' for empty condition after signal,
 * so a spurious signal (or signal consumed by another consumer) causes
 * this consumer to pop from an empty queue.
 */
int queue_pop(Queue *q, int *out);

/*
 * Resume a pop after being signaled. Called when signaled=1.
 * Should re-check if queue is still non-empty (but doesn't due to bug).
 */
int queue_resume_pop(Queue *q, int *out);

/* Check if queue is empty. */
int queue_is_empty(Queue *q);

/* Check if queue is full. */
int queue_is_full(Queue *q);

#endif /* QUEUE_H */
