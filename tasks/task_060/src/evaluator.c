#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include "stack.h"

/*
 * Evaluates a postfix expression given as space-separated tokens.
 * Tokens are either numbers or operators: + - * /
 * Returns 0 on success (result printed), or -1 on error.
 */
static int evaluate(const char *expr) {
    Stack s;
    stack_init(&s);

    char buf[256];
    strncpy(buf, expr, sizeof(buf) - 1);
    buf[sizeof(buf) - 1] = '\0';

    char *token = strtok(buf, " ");
    while (token != NULL) {
        if (strlen(token) == 1 && strchr("+-*/", token[0])) {
            /* Operator */
            double b, a;
            if (stack_pop(&s, &b) != 0 || stack_pop(&s, &a) != 0) {
                printf("ERROR: stack underflow\n");
                return -1;
            }

            double result;
            switch (token[0]) {
                case '+': result = a + b; break;
                case '-': result = a - b; break;
                case '*': result = a * b; break;
                case '/':
                    /* BUG: no division by zero check */
                    result = a / b;
                    break;
                default:
                    printf("ERROR: unknown operator %c\n", token[0]);
                    return -1;
            }

            /* Push result back — no overflow check here either */
            stack_push(&s, result);
        } else {
            /* Number — push onto stack, no overflow check */
            double val = atof(token);
            stack_push(&s, val);
        }

        token = strtok(NULL, " ");
    }

    double result;
    if (stack_pop(&s, &result) != 0) {
        printf("ERROR: empty expression\n");
        return -1;
    }

    if (!stack_is_empty(&s)) {
        printf("ERROR: too many operands\n");
        return -1;
    }

    /* Print integer result if no fractional part */
    if (result == (int)result) {
        printf("%d\n", (int)result);
    } else {
        printf("%.6f\n", result);
    }

    return 0;
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Usage: prog \"<postfix expression>\"\n");
        return 1;
    }

    int rc = evaluate(argv[1]);
    return rc == 0 ? 0 : 1;
}
