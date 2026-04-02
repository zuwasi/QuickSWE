"""Tokenizer — breaks expression strings into tokens.

Currently handles: numbers (int/float), +, -, *, /, whitespace.
TODO: Add support for: ^, ==, !=, <=, >=, <, >, (, ), and, or, not, true, false.
"""


class Token:
    """Represents a single token."""

    NUMBER = "NUMBER"
    OPERATOR = "OPERATOR"
    EOF = "EOF"

    def __init__(self, type_, value):
        self.type = type_
        self.value = value

    def __repr__(self):
        return f"Token({self.type}, {self.value!r})"

    def __eq__(self, other):
        if not isinstance(other, Token):
            return False
        return self.type == other.type and self.value == other.value


class Tokenizer:
    """Tokenizes mathematical expressions into a list of tokens.

    Currently supports: integers, floats, +, -, *, /
    """

    def __init__(self, text):
        self._text = text
        self._pos = 0

    def tokenize(self):
        """Convert the input text into a list of tokens.

        Returns:
            List of Token objects, ending with an EOF token.
        """
        tokens = []
        while self._pos < len(self._text):
            ch = self._text[self._pos]

            if ch.isspace():
                self._pos += 1
                continue

            if ch.isdigit() or (ch == '.' and self._pos + 1 < len(self._text)
                                and self._text[self._pos + 1].isdigit()):
                tokens.append(self._read_number())
                continue

            if ch in '+-*/':
                tokens.append(Token(Token.OPERATOR, ch))
                self._pos += 1
                continue

            raise SyntaxError(f"Unexpected character: {ch!r} at position {self._pos}")

        tokens.append(Token(Token.EOF, None))
        return tokens

    def _read_number(self):
        """Read a number (integer or float) from the current position."""
        start = self._pos
        has_dot = False
        while self._pos < len(self._text):
            ch = self._text[self._pos]
            if ch.isdigit():
                self._pos += 1
            elif ch == '.' and not has_dot:
                has_dot = True
                self._pos += 1
            else:
                break
        text = self._text[start:self._pos]
        value = float(text) if has_dot else int(text)
        return Token(Token.NUMBER, value)
