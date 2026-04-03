#ifndef STACK_H
#define STACK_H

#define MAX_STACK_SIZE 4

typedef struct {
    double data[MAX_STACK_SIZE];
    int top;
} Stack;

void stack_init(Stack *s);
int stack_push(Stack *s, double value);
int stack_pop(Stack *s, double *out);
int stack_is_empty(Stack *s);
int stack_size(Stack *s);

#endif
