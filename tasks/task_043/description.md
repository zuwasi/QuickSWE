# Feature Request: Line-Based Diff/Patch System for Documents

## Summary

We need a diff/patch system that can compute differences between two `Document` objects and apply those differences as patches. This is similar to how `diff` and `patch` work in Unix but implemented as a Python library.

## Current State

- `Document` class exists in `src/document.py` with basic text content management (line-based storage, line access, content retrieval).
- `src/diff.py` has a stub `DiffEngine` class with `compute_diff()` that raises `NotImplementedError`.
- `src/patch.py` has a stub `PatchEngine` class with `apply_patch()` and `reverse_patch()` that raise `NotImplementedError`.

## Requirements

### Diff Engine (`src/diff.py`)
1. Implement `compute_diff(doc_a: Document, doc_b: Document) -> list[DiffOp]` using a line-based diff algorithm.
2. Each `DiffOp` should be one of: `ADD`, `REMOVE`, or `KEEP` with the relevant line content and line numbers.
3. The diff should produce the minimal set of operations to transform `doc_a` into `doc_b`.
4. Handle edge cases: empty documents, identical documents, completely different documents.

### Patch Engine (`src/patch.py`)
1. Implement `apply_patch(doc: Document, diff_ops: list[DiffOp]) -> Document` that applies a diff to produce a new document.
2. Implement `reverse_patch(doc: Document, diff_ops: list[DiffOp]) -> Document` that reverses a diff (undoing the changes).
3. Applying a diff computed from `(A, B)` to `A` should produce `B`.
4. Reverse-patching `B` with the same diff should produce `A`.

### DiffOp
- `op`: one of `"add"`, `"remove"`, `"keep"`
- `line`: the text content of the line
- `line_no`: the line number in the source/target document

## Acceptance Criteria
- `compute_diff` produces correct operations for all cases.
- `apply_patch(A, diff(A, B)) == B` for all document pairs.
- `reverse_patch(B, diff(A, B)) == A` for all document pairs.
- Empty and identical documents handled correctly.
