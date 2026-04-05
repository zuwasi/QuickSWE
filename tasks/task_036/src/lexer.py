"""
Lexer/tokenizer for a C-like language.

Supports identifiers, integer and float literals, string literals,
single-line and multi-line comments, and all C operators including
compound assignment operators.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional


class TokenType(Enum):
    # Literals
    INTEGER = auto()
    FLOAT = auto()
    STRING = auto()
    IDENTIFIER = auto()

    # Keywords
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    RETURN = auto()
    INT = auto()
    FLOAT_KW = auto()
    VOID = auto()
    STRUCT = auto()
    TYPEDEF = auto()

    # Single-character operators
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    AMPERSAND = auto()
    PIPE = auto()
    CARET = auto()
    TILDE = auto()
    BANG = auto()
    ASSIGN = auto()
    LT = auto()
    GT = auto()
    DOT = auto()
    COMMA = auto()
    SEMICOLON = auto()
    COLON = auto()
    QUESTION = auto()

    # Two-character operators
    PLUS_ASSIGN = auto()
    MINUS_ASSIGN = auto()
    STAR_ASSIGN = auto()
    SLASH_ASSIGN = auto()
    PERCENT_ASSIGN = auto()
    AMPERSAND_ASSIGN = auto()
    PIPE_ASSIGN = auto()
    CARET_ASSIGN = auto()
    EQ = auto()
    NEQ = auto()
    LTE = auto()
    GTE = auto()
    LSHIFT = auto()
    RSHIFT = auto()
    AND = auto()
    OR = auto()
    INCREMENT = auto()
    DECREMENT = auto()
    ARROW = auto()

    # Three-character operators
    LSHIFT_ASSIGN = auto()
    RSHIFT_ASSIGN = auto()
    ELLIPSIS = auto()

    # Delimiters
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()

    # Special
    EOF = auto()
    ERROR = auto()


@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, {self.line}:{self.column})"


KEYWORDS = {
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "for": TokenType.FOR,
    "return": TokenType.RETURN,
    "int": TokenType.INT,
    "float": TokenType.FLOAT_KW,
    "void": TokenType.VOID,
    "struct": TokenType.STRUCT,
    "typedef": TokenType.TYPEDEF,
}

THREE_CHAR_OPS = {
    "<<=": TokenType.LSHIFT_ASSIGN,
    ">>=": TokenType.RSHIFT_ASSIGN,
    "...": TokenType.ELLIPSIS,
}

TWO_CHAR_OPS = {
    "+=": TokenType.PLUS_ASSIGN,
    "-=": TokenType.MINUS_ASSIGN,
    "*=": TokenType.STAR_ASSIGN,
    "/=": TokenType.SLASH_ASSIGN,
    "%=": TokenType.PERCENT_ASSIGN,
    "&=": TokenType.AMPERSAND_ASSIGN,
    "|=": TokenType.PIPE_ASSIGN,
    "^=": TokenType.CARET_ASSIGN,
    "==": TokenType.EQ,
    "!=": TokenType.NEQ,
    "<=": TokenType.LTE,
    ">=": TokenType.GTE,
    "<<": TokenType.LSHIFT,
    ">>": TokenType.RSHIFT,
    "&&": TokenType.AND,
    "||": TokenType.OR,
    "++": TokenType.INCREMENT,
    "--": TokenType.DECREMENT,
    "->": TokenType.ARROW,
}

SINGLE_CHAR_OPS = {
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
    "*": TokenType.STAR,
    "/": TokenType.SLASH,
    "%": TokenType.PERCENT,
    "&": TokenType.AMPERSAND,
    "|": TokenType.PIPE,
    "^": TokenType.CARET,
    "~": TokenType.TILDE,
    "!": TokenType.BANG,
    "=": TokenType.ASSIGN,
    "<": TokenType.LT,
    ">": TokenType.GT,
    ".": TokenType.DOT,
    ",": TokenType.COMMA,
    ";": TokenType.SEMICOLON,
    ":": TokenType.COLON,
    "?": TokenType.QUESTION,
}

DELIMITERS = {
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
    "{": TokenType.LBRACE,
    "}": TokenType.RBRACE,
    "[": TokenType.LBRACKET,
    "]": TokenType.RBRACKET,
}


class Lexer:
    """Tokenizer for a C-like language."""

    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []

    def _peek(self, offset: int = 0) -> Optional[str]:
        idx = self.pos + offset
        if idx < len(self.source):
            return self.source[idx]
        return None

    def _advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def _skip_whitespace(self):
        while self.pos < len(self.source) and self.source[self.pos] in " \t\n\r":
            self._advance()

    def _skip_line_comment(self):
        while self.pos < len(self.source) and self.source[self.pos] != "\n":
            self._advance()

    def _skip_block_comment(self):
        while self.pos < len(self.source):
            if self.source[self.pos] == "*" and self._peek(1) == "/":
                self._advance()
                self._advance()
                return
            self._advance()
        self.tokens.append(Token(TokenType.ERROR, "unterminated block comment", self.line, self.column))

    def _read_string(self) -> Token:
        start_line = self.line
        start_col = self.column
        self._advance()  # skip opening quote
        chars = []
        while self.pos < len(self.source):
            ch = self.source[self.pos]
            if ch == '"':
                self._advance()
                return Token(TokenType.STRING, "".join(chars), start_line, start_col)
            if ch == '\\':
                self._advance()
                if self.pos < len(self.source):
                    esc = self._advance()
                    escape_map = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", '"': '"', "0": "\0"}
                    chars.append(escape_map.get(esc, esc))
                continue
            if ch == '\n':
                return Token(TokenType.ERROR, "unterminated string", start_line, start_col)
            chars.append(self._advance())
        return Token(TokenType.ERROR, "unterminated string", start_line, start_col)

    def _read_number(self) -> Token:
        start_line = self.line
        start_col = self.column
        chars = []
        is_float = False

        if self.source[self.pos] == '0' and self._peek(1) in ('x', 'X'):
            chars.append(self._advance())
            chars.append(self._advance())
            while self.pos < len(self.source) and self.source[self.pos] in "0123456789abcdefABCDEF_":
                if self.source[self.pos] != '_':
                    chars.append(self._advance())
                else:
                    self._advance()
            return Token(TokenType.INTEGER, "".join(chars), start_line, start_col)

        while self.pos < len(self.source) and (self.source[self.pos].isdigit() or self.source[self.pos] == '_'):
            if self.source[self.pos] != '_':
                chars.append(self._advance())
            else:
                self._advance()

        if self.pos < len(self.source) and self.source[self.pos] == '.':
            next_ch = self._peek(1)
            if next_ch is not None and next_ch.isdigit():
                is_float = True
                chars.append(self._advance())
                while self.pos < len(self.source) and (self.source[self.pos].isdigit() or self.source[self.pos] == '_'):
                    if self.source[self.pos] != '_':
                        chars.append(self._advance())
                    else:
                        self._advance()

        if self.pos < len(self.source) and self.source[self.pos] in ('e', 'E'):
            is_float = True
            chars.append(self._advance())
            if self.pos < len(self.source) and self.source[self.pos] in ('+', '-'):
                chars.append(self._advance())
            while self.pos < len(self.source) and self.source[self.pos].isdigit():
                chars.append(self._advance())

        tok_type = TokenType.FLOAT if is_float else TokenType.INTEGER
        return Token(tok_type, "".join(chars), start_line, start_col)

    def _read_identifier(self) -> Token:
        start_line = self.line
        start_col = self.column
        chars = []
        while self.pos < len(self.source) and (self.source[self.pos].isalnum() or self.source[self.pos] == '_'):
            chars.append(self._advance())
        word = "".join(chars)
        tok_type = KEYWORDS.get(word, TokenType.IDENTIFIER)
        return Token(tok_type, word, start_line, start_col)

    def _read_operator(self) -> Token:
        start_line = self.line
        start_col = self.column

        ch = self.source[self.pos]

        # Check two-character operators first
        two_chars = self.source[self.pos:self.pos + 2]
        if len(two_chars) == 2 and two_chars in TWO_CHAR_OPS:
            self._advance()
            self._advance()
            return Token(TWO_CHAR_OPS[two_chars], two_chars, start_line, start_col)

        # Check single-character operators
        if ch in SINGLE_CHAR_OPS:
            self._advance()
            return Token(SINGLE_CHAR_OPS[ch], ch, start_line, start_col)

        self._advance()
        return Token(TokenType.ERROR, ch, start_line, start_col)

    def tokenize(self) -> List[Token]:
        """Tokenize the entire source and return list of tokens."""
        self.tokens = []

        while self.pos < len(self.source):
            self._skip_whitespace()
            if self.pos >= len(self.source):
                break

            ch = self.source[self.pos]

            # Comments
            if ch == '/' and self._peek(1) == '/':
                self._advance()
                self._advance()
                self._skip_line_comment()
                continue
            if ch == '/' and self._peek(1) == '*':
                self._advance()
                self._advance()
                self._skip_block_comment()
                continue

            # Strings
            if ch == '"':
                self.tokens.append(self._read_string())
                continue

            # Character literals
            if ch == "'":
                start_line = self.line
                start_col = self.column
                self._advance()
                if self.pos < len(self.source):
                    if self.source[self.pos] == '\\':
                        self._advance()
                        if self.pos < len(self.source):
                            self._advance()
                    else:
                        self._advance()
                if self.pos < len(self.source) and self.source[self.pos] == "'":
                    self._advance()
                self.tokens.append(Token(TokenType.INTEGER, "char", start_line, start_col))
                continue

            # Numbers
            if ch.isdigit():
                self.tokens.append(self._read_number())
                continue

            # Identifiers and keywords
            if ch.isalpha() or ch == '_':
                self.tokens.append(self._read_identifier())
                continue

            # Delimiters
            if ch in DELIMITERS:
                self._advance()
                self.tokens.append(Token(DELIMITERS[ch], ch, self.line, self.column - 1))
                continue

            # Operators
            if ch in SINGLE_CHAR_OPS or ch in "!<>=&|+-":
                self.tokens.append(self._read_operator())
                continue

            # Unknown character
            self._advance()
            self.tokens.append(Token(TokenType.ERROR, ch, self.line, self.column - 1))

        self.tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return self.tokens


def tokenize(source: str) -> List[Token]:
    """Convenience function to tokenize source code."""
    lexer = Lexer(source)
    return lexer.tokenize()


def format_tokens(tokens: List[Token]) -> str:
    """Format token list as a readable string for debugging."""
    lines = []
    for tok in tokens:
        if tok.type == TokenType.EOF:
            lines.append(f"  EOF")
        else:
            lines.append(f"  {tok.type.name:20s} {tok.value!r:20s} @ {tok.line}:{tok.column}")
    return "\n".join(lines)


class TokenStream:
    """Wrapper around token list providing stream-like access for parsers."""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]

    def advance(self) -> Token:
        tok = self.peek()
        if tok.type != TokenType.EOF:
            self.pos += 1
        return tok

    def expect(self, token_type: TokenType) -> Token:
        tok = self.advance()
        if tok.type != token_type:
            raise SyntaxError(
                f"Expected {token_type.name} but got {tok.type.name} ({tok.value!r}) "
                f"at {tok.line}:{tok.column}"
            )
        return tok

    def match(self, *token_types: TokenType) -> Optional[Token]:
        if self.peek().type in token_types:
            return self.advance()
        return None

    def at_end(self) -> bool:
        return self.peek().type == TokenType.EOF

    def remaining(self) -> List[Token]:
        return self.tokens[self.pos:]
