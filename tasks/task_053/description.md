# Feature Request: Tokenizer Should Handle Escaping and Quoting

## Summary
Our string tokenizer works great for simple CSV-like splitting but users need to
be able to include the delimiter character in their data. Two common conventions
need to be supported:

1. **Backslash escaping**: `\,` should produce a literal comma, not split
2. **Quoted strings**: content inside double quotes `"..."` should be treated as
   literal — delimiters inside quotes don't cause a split

## Current Behavior
- `"hello,world,foo"` with delimiter `,` → `["hello", "world", "foo"]` ✓
- `"hello\,world,foo"` with delimiter `,` → `["hello\", "world", "foo"]` ✗
- `'"a,b",c'` with delimiter `,` → `['"a', 'b"', 'c']` ✗

## Expected Behavior
- `"hello\,world,foo"` → `["hello,world", "foo"]`
- `'"a,b",c'` → `["a,b", "c"]`
- `'"hello \"world\"",test'` → `["hello \"world\"", "test"]` (escaped quotes inside quotes)

## Notes
- The backslash itself can be escaped: `\\` produces a literal backslash
- The tokenizer should allocate result strings that have escape sequences resolved
  (i.e., the output tokens should not contain the backslash escape characters)
- Empty tokens between delimiters should be preserved
