# Bug Report: Text Processing Crashes on Some Files

## Summary
The text file processing pipeline crashes on some files but not others. It seems random — the same file structure works fine for some content but fails for others. We get UnicodeDecodeError or garbled output.

## Steps to Reproduce
1. Process a text file containing emoji or CJK characters
2. If the file is large enough that chunked reading kicks in, it may crash
3. Smaller files or pure ASCII files always work fine

## Expected Behavior
All valid UTF-8 files should be processed correctly regardless of size.

## Additional Notes
- We use chunked reading for memory efficiency on large files
- The chunk size is configurable, defaults to 4096 bytes
- Error happens in the decoder layer — maybe an encoding detection issue?
- Some team members suspect the line splitter is corrupting data
- Works fine when chunk size is set very large (whole file in one chunk)
