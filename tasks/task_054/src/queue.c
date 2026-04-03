#include "queue.h"
#include <string.h>

void queue_init(Queue *q, int capacity) {
    memset(q, 0, sizeof(Queue));
    q->capacity = (capacity > QUEUE_MAX_SIZE) ? QUEUE_MAX_SIZE : capacity;
    q->head = 0;
    q->tail = 0;
    q->count = 0;
    q->waiting_pop = 0;
    q->signaled = 0;
}

int queue_push(Queue *q, int item) {
    if (q->count >= q->capacity) {
        return -1; /* full */
    }
    q->items[q->tail] = item;
    q->tail = (q->tail + 1) % q->capacity;
    q->count++;

    /* Signal any waiting consumer */
    if (q->waiting_pop) {
        q->signaled = 1;
    }
    return 0;
}

int queue_pop(Queue *q, int *out) {
    /*
     * BUG: This uses a single 'if' check. In a concurrent scenario
     * (simulated via interleaving), after being signaled, we should
     * re-check if the queue is STILL non-empty. Another consumer
     * might have already taken the item between signal and resume.
     *
     * Correct pattern: while (queue_is_empty(q)) { wait; }
     * Buggy pattern:   if (queue_is_empty(q)) { wait; }  // then proceed blindly
     */
    if (q->count == 0) {
        /* Queue is empty - set waiting flag */
        q->waiting_pop = 1;
        return -2; /* WAITING */
    }

    *out = q->items[q->head];
    q->head = (q->head + 1) % q->capacity;
    q->count--;
    return 0;
}

int queue_resume_pop(Queue *q, int *out) {
    /*
     * BUG: After being signaled, this does NOT re-check if queue is empty.
     * It blindly proceeds to dequeue, which will read garbage and underflow
     * the count if another consumer already took the item.
     *
     * Fix: Should check q->count == 0 again and return -2 if still empty.
     */
    q->waiting_pop = 0;
    q->signaled = 0;

    /* BUG: No re-check of emptiness! Just blindly dequeues. */
    *out = q->items[q->head];
    q->head = (q->head + 1) % q->capacity;
    q->count--;
    return 0;
}

int queue_is_empty(Queue *q) {
    return q->count == 0;
}

int queue_is_full(Queue *q) {
    return q->count >= q->capacity;
}
