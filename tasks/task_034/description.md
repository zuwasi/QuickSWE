# Task 034: Expression Evaluator with Operator Precedence

## Overview

Fix and extend a math expression evaluator. The current parser treats all operators as left-to-right with no precedence (so `2+3*4` gives 20 instead of 14). Refactor the parser to handle proper operator precedence and add new operators.

## Requirements

1. **Operator precedence** (lowest to highest):
   - `or` (boolean)
   - `and` (boolean)
   - `not` (unary boolean, prefix)
   - `==`, `<`, `>`, `<=`, `>=`, `!=` (comparison)
   - `+`, `-` (addition/subtraction)
   - `*`, `/` (multiplication/division)
   - `^` (power — **right-associative**)
   - unary `-` (negation, prefix)
   - parentheses `()`

2. **New AST nodes needed**:
   - `UnaryOpNode(op, operand)` — for unary minus and `not`
   - `ComparisonNode(op, left, right)` — for comparison operators
   - `BooleanNode(op, left, right)` — for `and`, `or`

3. **Tokenizer updates**: Must handle `^`, `==`, `!=`, `<=`, `>=`, `<`, `>`, `(`, `)`, `and`, `or`, `not`, `true`, `false`.

4. **Evaluator updates**: Must evaluate all new node types. Division by zero should raise `ZeroDivisionError`. Comparisons return `True`/`False`. Boolean operators work on truthy/falsy values.

5. **Formatter updates**: Must format all new node types back to string representation.

## Existing Code

- `tokenizer.py` tokenizes basic math expressions (+, -, *, /, numbers).
- `parser.py` parses left-to-right with no precedence.
- `ast_nodes.py` has NumberNode and BinOpNode.
- `evaluator.py` evaluates NumberNode and BinOpNode.
- `formatter.py` formats expressions as strings.

## Constraints

- Pure Python.
- Power operator `^` is right-associative: `2^3^2` = `2^(3^2)` = 512, not `(2^3)^2` = 64.
- `true` and `false` are boolean literals.
