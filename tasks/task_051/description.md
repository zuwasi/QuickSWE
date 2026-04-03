# Bug Report: Dynamic Array Crashes on First Insert

## Summary
Our dynamic array library segfaults or produces garbage values intermittently.
Sometimes the first `push()` works, sometimes it doesn't. Users also report being
able to read values at indices way beyond what they inserted, getting random memory
contents back instead of an error.

## Steps to Reproduce
1. Create a new dynamic array with `dynarray_init()`
2. Push a few values
3. Try to read values — sometimes garbage is returned
4. Try to read at an index that was never written — no error, just garbage

## Expected Behavior
- Push should reliably grow the array
- Get at valid indices returns correct values
- Get at invalid indices returns an error code

## Environment
- GCC on Windows/Linux
- Crashes are intermittent, sometimes works fine with small arrays

## Reporter Notes
I think there's something wrong with the memory allocation but I can't pin it down.
The array seems to work fine if I manually set an initial capacity before pushing,
but the default initialization path is broken.
