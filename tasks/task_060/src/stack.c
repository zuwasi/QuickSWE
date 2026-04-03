#include "stack.h"

void stack_init(Stack *s) {
    s->top = -1;
}

int stack_push(Stack *s, double value) {
    /* BUG: no overflow check — blindly increments top and writes past array */
    s->top++;
    s->data[s->top] = value;
    return 0;  /* always "succeeds" */
}

int stack_pop(Stack *s, double *out) {
    if (s->top < 0) {
        return -1;  /* underflow */
    }
    *out = s->data[s->top];
    s->top--;
    return 0;
}

int stack_is_empty(Stack *s) {
    return s->top < 0;
}

int stack_size(Stack *s) {
    return s->top + 1;
}
