"""Editor that wraps a Document with higher-level operations."""

from src.document import Document


class Editor:
    """Text editor providing high-level editing operations on a Document."""

    def __init__(self, document: Document = None):
        self._document = document or Document()

    @property
    def document(self) -> Document:
        return self._document

    @property
    def text(self) -> str:
        """Current document text."""
        return self._document.content

    def insert(self, position: int, text: str) -> None:
        """Insert text at position."""
        self._document.insert(position, text)

    def delete(self, position: int, length: int) -> str:
        """Delete length characters at position. Returns deleted text."""
        return self._document.delete(position, length)

    def append(self, text: str) -> None:
        """Append text to end of document."""
        self._document.insert(len(self._document), text)

    def replace(self, start: int, length: int, new_text: str) -> str:
        """Replace a range of text. Returns the original text."""
        old_text = self._document.delete(start, length)
        self._document.insert(start, new_text)
        return old_text

    def clear(self) -> str:
        """Clear the entire document. Returns the old content."""
        old = self._document.content
        self._document.delete(0, len(self._document))
        return old

    def find(self, query: str) -> int:
        """Find the first occurrence of query. Returns position or -1."""
        return self._document.content.find(query)

    def word_count(self) -> int:
        """Count words in the document."""
        text = self._document.content.strip()
        if not text:
            return 0
        return len(text.split())
