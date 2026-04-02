"""Document model for the text editor."""


class Document:
    """Represents a text document with basic editing operations."""

    def __init__(self, content: str = ""):
        self._content = content
        self._name = "Untitled"

    @property
    def content(self) -> str:
        return self._content

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    def insert(self, position: int, text: str) -> None:
        """Insert text at the given position.

        Position is clamped to valid range [0, len(content)].
        """
        pos = max(0, min(position, len(self._content)))
        self._content = self._content[:pos] + text + self._content[pos:]

    def delete(self, position: int, length: int) -> str:
        """Delete `length` characters starting at position.

        Returns the deleted text.
        Position and length are clamped to valid range.
        """
        pos = max(0, min(position, len(self._content)))
        end = min(pos + max(0, length), len(self._content))
        deleted = self._content[pos:end]
        self._content = self._content[:pos] + self._content[end:]
        return deleted

    def get_text(self, start: int = 0, end: int = None) -> str:
        """Get a slice of the document text."""
        if end is None:
            end = len(self._content)
        return self._content[max(0, start):min(end, len(self._content))]

    def __len__(self):
        return len(self._content)

    def __repr__(self):
        preview = self._content[:50] + "..." if len(self._content) > 50 else self._content
        return f"Document(name={self._name!r}, len={len(self._content)}, content={preview!r})"
