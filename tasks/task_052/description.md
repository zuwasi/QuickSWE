# String Tokenizer – Incorrect Escape Sequence Handling

## Problem

A string tokenizer splits input strings by a delimiter, but also supports escape
sequences so the delimiter character can appear inside tokens. The escape character
is backslash (`\`).

Users report:

1. Escaped delimiters are not correctly preserved — the token is split at an
   escaped delimiter instead of including it as a literal character.
2. Consecutive escape characters (`\\`) are not handled: `\\` should produce a
   literal backslash, but the tokenizer either drops it or treats the next
   character as escaped.
3. An escape at the very end of the string causes incorrect output.

## Files

- `src/tokenizer.hpp` — tokenizer class
- `src/main.cpp` — driver program

## Expected Behaviour

- `split("a,b,c", ',')` → `["a", "b", "c"]`
- `split("a\\,b,c", ',')` → `["a,b", "c"]` (escaped comma is literal)
- `split("a\\\\,b", ',')` → `["a\\", "b"]` (escaped backslash + real delimiter)
- `split("a\\", ',')` → `["a\\"]` (trailing escape preserved as literal)
