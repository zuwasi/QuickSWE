# Bug: File reader defaults to ASCII instead of UTF-8

## Description

The `read_text_file(path, encoding=None)` function reads a text file and returns its contents. When `encoding` is `None`, it should default to `'utf-8'`. Instead, it defaults to `'ascii'`, causing a `UnicodeDecodeError` when reading files that contain non-ASCII characters.

## Expected Behavior

- `read_text_file("file.txt")` (no encoding specified) should read the file as UTF-8.
- Files containing characters like `café`, `naïve`, or `über` should be read correctly.

## Actual Behavior

- `read_text_file("file.txt")` raises `UnicodeDecodeError: 'ascii' codec can't decode byte ...`

## How to Reproduce

```python
from file_reader import read_text_file

# Create a file with UTF-8 content
with open("test.txt", "w", encoding="utf-8") as f:
    f.write("café au lait")

read_text_file("test.txt")  # UnicodeDecodeError
```
