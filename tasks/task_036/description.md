# Task 036: Compiler Tokenizer Multi-Character Operator Handling

## Description

A lexer/tokenizer for a C-like language incorrectly handles multi-character operators.
The greedy matching algorithm doesn't look ahead far enough for three-character operators
like `>>=`, `<<=`, and `...`. As a result, `>>=` is split into `>>` and `=`, `<<=` becomes
`<<` and `=`, and similar misparses occur for other compound operators.

## Bug

The tokenizer's operator matching logic uses a two-character lookahead maximum when it
should use three characters. This causes all three-character operators to be incorrectly
tokenized as a two-character operator followed by a single-character operator.

## Expected Behavior

All valid multi-character operators (up to 3 characters) should be matched as single tokens,
with the longest match taking priority.
