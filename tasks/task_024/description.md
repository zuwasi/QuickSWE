# Task 024: Add Undo/Redo with Command Pattern to Editor

## Current State

Simple text editor spread across two files:

- `src/document.py` — `Document` class that holds text content with `insert(pos, text)` and `delete(pos, length)` methods
- `src/editor.py` — `Editor` class wrapping `Document` with higher-level editing operations

Everything works but there's no way to undo anything. Users have been asking for undo/redo for a while.

## Feature Request

Implement proper undo/redo using the Command pattern. The idea:

- Each editing operation (insert, delete) should create a command object that knows how to do and undo itself
- The editor maintains an undo stack and a redo stack
- `editor.undo()` pops the last command and reverses it
- `editor.redo()` re-applies an undone command
- When a new edit happens after some undos, the redo stack clears (standard behaviour)

Also need transaction support — sometimes we want to group several edits into one undoable unit. Something like:

```python
editor.begin_transaction()
editor.insert(0, "Hello")
editor.insert(5, " World")
editor.end_transaction()
editor.undo()  # undoes both inserts at once
```

## Constraints

- Don't change the Document class API — insert/delete should still work the same way
- Editor's basic editing methods must continue working as before
- Command objects should live in their own module or in the editor module

## Acceptance Criteria

- [ ] `editor.undo()` reverses the last edit
- [ ] `editor.redo()` re-applies an undone edit
- [ ] Multiple undos work in sequence
- [ ] Redo stack clears on new edit after undo
- [ ] Transaction grouping works — multiple edits undo as one
- [ ] Basic insert/delete operations unchanged
