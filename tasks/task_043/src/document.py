"""Document class with line-based text content storage."""


class Document:
    """Represents a text document as a list of lines."""

    def __init__(self, content: str = ""):
        """Initialize document from a string.

        Args:
            content: The text content. Split into lines internally.
        """
        if content:
            self._lines = content.splitlines()
        else:
            self._lines = []

    @classmethod
    def from_lines(cls, lines: list[str]) -> "Document":
        """Create a Document from a list of line strings."""
        doc = cls()
        doc._lines = list(lines)
        return doc

    @property
    def lines(self) -> list[str]:
        """Return a copy of the lines."""
        return list(self._lines)

    @property
    def line_count(self) -> int:
        """Return the number of lines."""
        return len(self._lines)

    def get_line(self, index: int) -> str:
        """Get a line by zero-based index.

        Raises:
            IndexError: If index is out of range.
        """
        return self._lines[index]

    @property
    def content(self) -> str:
        """Return the full content as a single string with newlines."""
        return "\n".join(self._lines)

    def is_empty(self) -> bool:
        """Check if the document has no content."""
        return len(self._lines) == 0

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Document):
            return NotImplemented
        return self._lines == other._lines

    def __repr__(self) -> str:
        preview = self._lines[:3]
        suffix = "..." if len(self._lines) > 3 else ""
        return f"Document(lines={len(self._lines)}, preview={preview}{suffix})"
