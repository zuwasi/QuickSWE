"""Diff engine for computing line-based differences between documents."""

from dataclasses import dataclass
from enum import Enum

from .document import Document


class OpType(Enum):
    ADD = "add"
    REMOVE = "remove"
    KEEP = "keep"


@dataclass
class DiffOp:
    """Represents a single diff operation.

    Attributes:
        op: The type of operation (add, remove, keep).
        line: The text content of the line.
        line_no: The line number (zero-based) in the relevant document.
    """
    op: OpType
    line: str
    line_no: int


class DiffEngine:
    """Computes line-based diffs between two Documents.

    Should implement a longest-common-subsequence based diff algorithm
    that produces a minimal list of DiffOp operations to transform
    doc_a into doc_b.
    """

    def compute_diff(self, doc_a: Document, doc_b: Document) -> list[DiffOp]:
        """Compute the diff operations to transform doc_a into doc_b.

        Args:
            doc_a: The original document.
            doc_b: The modified document.

        Returns:
            A list of DiffOp operations (add, remove, keep).
        """
        raise NotImplementedError("DiffEngine.compute_diff is not yet implemented")
