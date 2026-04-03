# Bug: Stack-based Expression Evaluator Overflow

## Description

A postfix (Reverse Polish Notation) expression evaluator uses a fixed-size stack. It has two bugs:

1. **No stack overflow check**: The `push` function does not check if the stack is full before pushing. When evaluating expressions with many operands (more than `MAX_STACK_SIZE`), it writes past the array boundary, causing corruption or crashes.

2. **Division by zero not handled**: The evaluator does not check for a zero divisor when processing the `/` operator, leading to undefined behavior.

The evaluator should return an error code when overflow or division by zero occurs, printing `ERROR: <message>` to stdout instead of crashing.

## Expected Behavior

- Expressions that would overflow the stack produce `ERROR: stack overflow`.
- Expressions containing division by zero produce `ERROR: division by zero`.
- Valid expressions produce the correct numeric result.

## Actual Behavior

- Stack overflow causes a crash or silent memory corruption.
- Division by zero causes a crash or undefined behavior.

## Files

- `src/stack.h` — stack definitions (MAX_STACK_SIZE = 4)
- `src/stack.c` — stack implementation (~50 lines)
- `src/evaluator.c` — postfix evaluator (~80 lines) with main()
