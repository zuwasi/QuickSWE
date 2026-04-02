"""Patch engine for applying and reversing diffs on documents."""

from .document import Document
from .diff import DiffOp


class PatchError(Exception):
    """Raised when a patch cannot be applied."""
    pass


class PatchEngine:
    """Applies and reverses diffs on Documents.

    Given a list of DiffOp produced by DiffEngine.compute_diff(A, B):
    - apply_patch(A, ops) should produce B
    - reverse_patch(B, ops) should produce A
    """

    def apply_patch(self, doc: Document, diff_ops: list[DiffOp]) -> Document:
        """Apply diff operations to a document to produce a new document.

        Args:
            doc: The original document (should match the source of the diff).
            diff_ops: The diff operations to apply.

        Returns:
            A new Document with the diff applied.

        Raises:
            PatchError: If the patch cannot be applied cleanly.
        """
        raise NotImplementedError("PatchEngine.apply_patch is not yet implemented")

    def reverse_patch(self, doc: Document, diff_ops: list[DiffOp]) -> Document:
        """Reverse-apply diff operations to undo changes.

        If diff was computed from (A, B), then reverse_patch(B, diff) should return A.

        Args:
            doc: The modified document (should match the target of the diff).
            diff_ops: The diff operations to reverse.

        Returns:
            A new Document with the diff reversed.

        Raises:
            PatchError: If the reverse patch cannot be applied cleanly.
        """
        raise NotImplementedError("PatchEngine.reverse_patch is not yet implemented")
