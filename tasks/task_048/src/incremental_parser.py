"""
Incremental parser for a simple expression/statement language.

Supports parsing a sequence of statements, error recovery at statement
boundaries, and incremental re-parsing of modified text regions.

Grammar:
    program     := statement*
    statement   := assignment | expr_stmt
    assignment  := IDENT '=' expr ';'
    expr_stmt   := expr ';'
    expr        := term (('+' | '-') term)*
    term        := factor (('*' | '/') factor)*
    factor      := NUMBER | IDENT | '(' expr ')' | '-' factor
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple, Any


class TokenKind(Enum):
    NUMBER = auto()
    IDENT = auto()
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    EQUALS = auto()
    LPAREN = auto()
    RPAREN = auto()
    SEMICOLON = auto()
    EOF = auto()
    ERROR = auto()


@dataclass
class Token:
    kind: TokenKind
    value: str
    pos: int
    length: int


class Lexer:
    """Simple tokenizer for the expression language."""

    def __init__(self, source: str):
        self.source = source
        self.pos = 0

    def _skip_ws(self):
        while self.pos < len(self.source) and self.source[self.pos] in " \t\n\r":
            self.pos += 1

    def next_token(self) -> Token:
        self._skip_ws()
        if self.pos >= len(self.source):
            return Token(TokenKind.EOF, "", self.pos, 0)

        ch = self.source[self.pos]
        start = self.pos

        if ch.isdigit():
            while self.pos < len(self.source) and (self.source[self.pos].isdigit() or self.source[self.pos] == '.'):
                self.pos += 1
            return Token(TokenKind.NUMBER, self.source[start:self.pos], start, self.pos - start)

        if ch.isalpha() or ch == '_':
            while self.pos < len(self.source) and (self.source[self.pos].isalnum() or self.source[self.pos] == '_'):
                self.pos += 1
            return Token(TokenKind.IDENT, self.source[start:self.pos], start, self.pos - start)

        self.pos += 1
        simple = {
            '+': TokenKind.PLUS, '-': TokenKind.MINUS,
            '*': TokenKind.STAR, '/': TokenKind.SLASH,
            '=': TokenKind.EQUALS, '(': TokenKind.LPAREN,
            ')': TokenKind.RPAREN, ';': TokenKind.SEMICOLON,
        }
        if ch in simple:
            return Token(simple[ch], ch, start, 1)

        return Token(TokenKind.ERROR, ch, start, 1)

    def tokenize_all(self) -> List[Token]:
        tokens = []
        while True:
            tok = self.next_token()
            tokens.append(tok)
            if tok.kind == TokenKind.EOF:
                break
        return tokens


class NodeKind(Enum):
    PROGRAM = auto()
    ASSIGNMENT = auto()
    EXPR_STMT = auto()
    BINARY_OP = auto()
    UNARY_OP = auto()
    NUMBER_LIT = auto()
    IDENT_REF = auto()
    ERROR_NODE = auto()


@dataclass
class ASTNode:
    kind: NodeKind
    value: str = ""
    children: List["ASTNode"] = field(default_factory=list)
    pos: int = 0
    length: int = 0
    error_message: str = ""

    def __repr__(self):
        if self.children:
            kids = ", ".join(repr(c) for c in self.children)
            return f"{self.kind.name}({self.value}, [{kids}])"
        return f"{self.kind.name}({self.value})"


class ParseError(Exception):
    def __init__(self, message: str, pos: int):
        super().__init__(message)
        self.pos = pos


class IncrementalParser:
    """Parser with error recovery and incremental parsing support."""

    def __init__(self):
        self.tokens: List[Token] = []
        self.pos: int = 0
        self.errors: List[str] = []
        self.source: str = ""
        self._parsed_statements: List[ASTNode] = []

    def _peek(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token(TokenKind.EOF, "", len(self.source), 0)

    def _advance(self) -> Token:
        tok = self._peek()
        if tok.kind != TokenKind.EOF:
            self.pos += 1
        return tok

    def _expect(self, kind: TokenKind) -> Token:
        tok = self._peek()
        if tok.kind != kind:
            raise ParseError(
                f"Expected {kind.name} but got {tok.kind.name} '{tok.value}'",
                tok.pos
            )
        return self._advance()

    def _match(self, kind: TokenKind) -> Optional[Token]:
        if self._peek().kind == kind:
            return self._advance()
        return None

    def parse(self, source: str) -> ASTNode:
        """Parse the source code and return the AST."""
        self.source = source
        self.tokens = Lexer(source).tokenize_all()
        self.pos = 0
        self.errors = []
        self._parsed_statements = []

        statements = self._parse_program()
        return ASTNode(
            kind=NodeKind.PROGRAM,
            children=statements,
            pos=0,
            length=len(source),
        )

    def _parse_program(self) -> List[ASTNode]:
        """Parse a sequence of statements with error recovery."""
        statements: List[ASTNode] = []

        while self._peek().kind != TokenKind.EOF:
            try:
                stmt = self._parse_statement()
                statements.append(stmt)
                self._parsed_statements.append(stmt)
            except ParseError as e:
                self.errors.append(str(e))
                error_node = ASTNode(
                    kind=NodeKind.ERROR_NODE,
                    value=str(e),
                    pos=e.pos,
                    error_message=str(e),
                )
                statements, error_node = self._recover_from_error(
                    statements, error_node
                )
                if error_node:
                    statements.append(error_node)

        return statements

    def _recover_from_error(self, statements: List[ASTNode],
                            error_node: ASTNode) -> Tuple[List[ASTNode], Optional[ASTNode]]:
        """
        Recover from a parse error by finding the next statement boundary.
        """
        # Reset all parsed state and skip to next semicolon
        statements = []
        self._parsed_statements = []

        while self._peek().kind not in (TokenKind.SEMICOLON, TokenKind.EOF):
            self._advance()
        if self._peek().kind == TokenKind.SEMICOLON:
            self._advance()

        return statements, error_node

    def _parse_statement(self) -> ASTNode:
        """Parse a single statement."""
        # Try assignment: IDENT = expr ;
        if (self._peek().kind == TokenKind.IDENT and
                self.pos + 1 < len(self.tokens) and
                self.tokens[self.pos + 1].kind == TokenKind.EQUALS):
            return self._parse_assignment()

        return self._parse_expr_stmt()

    def _parse_assignment(self) -> ASTNode:
        name_tok = self._expect(TokenKind.IDENT)
        self._expect(TokenKind.EQUALS)
        expr = self._parse_expr()
        self._expect(TokenKind.SEMICOLON)
        return ASTNode(
            kind=NodeKind.ASSIGNMENT,
            value=name_tok.value,
            children=[expr],
            pos=name_tok.pos,
        )

    def _parse_expr_stmt(self) -> ASTNode:
        expr = self._parse_expr()
        semi = self._expect(TokenKind.SEMICOLON)
        return ASTNode(
            kind=NodeKind.EXPR_STMT,
            children=[expr],
            pos=expr.pos,
        )

    def _parse_expr(self) -> ASTNode:
        """Parse addition/subtraction expression."""
        left = self._parse_term()

        while self._peek().kind in (TokenKind.PLUS, TokenKind.MINUS):
            op = self._advance()
            right = self._parse_term()
            left = ASTNode(
                kind=NodeKind.BINARY_OP,
                value=op.value,
                children=[left, right],
                pos=left.pos,
            )

        return left

    def _parse_term(self) -> ASTNode:
        """Parse multiplication/division expression."""
        left = self._parse_factor()

        while self._peek().kind in (TokenKind.STAR, TokenKind.SLASH):
            op = self._advance()
            right = self._parse_factor()
            left = ASTNode(
                kind=NodeKind.BINARY_OP,
                value=op.value,
                children=[left, right],
                pos=left.pos,
            )

        return left

    def _parse_factor(self) -> ASTNode:
        """Parse a factor (number, ident, parenthesized expr, unary minus)."""
        tok = self._peek()

        if tok.kind == TokenKind.NUMBER:
            self._advance()
            return ASTNode(kind=NodeKind.NUMBER_LIT, value=tok.value, pos=tok.pos)

        if tok.kind == TokenKind.IDENT:
            self._advance()
            return ASTNode(kind=NodeKind.IDENT_REF, value=tok.value, pos=tok.pos)

        if tok.kind == TokenKind.LPAREN:
            self._advance()
            expr = self._parse_expr()
            self._expect(TokenKind.RPAREN)
            return expr

        if tok.kind == TokenKind.MINUS:
            self._advance()
            operand = self._parse_factor()
            return ASTNode(
                kind=NodeKind.UNARY_OP,
                value="-",
                children=[operand],
                pos=tok.pos,
            )

        raise ParseError(f"Unexpected token: {tok.kind.name} '{tok.value}'", tok.pos)

    def update(self, source: str, change_start: int, change_end: int,
               new_text: str) -> ASTNode:
        """
        Incrementally update the parse tree after a text edit.
        For simplicity, re-parses the entire source with the applied edit.
        """
        new_source = source[:change_start] + new_text + source[change_end:]
        return self.parse(new_source)

    def get_errors(self) -> List[str]:
        return list(self.errors)

    def has_errors(self) -> bool:
        return len(self.errors) > 0


def count_nodes(node: ASTNode, kind: Optional[NodeKind] = None) -> int:
    """Count nodes in an AST, optionally filtered by kind."""
    count = 0
    if kind is None or node.kind == kind:
        count = 1
    for child in node.children:
        count += count_nodes(child, kind)
    return count


def collect_statements(node: ASTNode) -> List[ASTNode]:
    """Collect all statement nodes from a program."""
    if node.kind == NodeKind.PROGRAM:
        return list(node.children)
    return []
