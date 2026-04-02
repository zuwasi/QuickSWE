"""Parser — converts tokens into an AST.

CURRENT BEHAVIOR (BROKEN): Parses all operators left-to-right with NO precedence.
So `2 + 3 * 4` parses as `(2 + 3) * 4` = 20 instead of `2 + (3 * 4)` = 14.

TODO: Refactor to use proper operator precedence parsing (e.g., recursive descent
with different levels for each precedence group, or Pratt parsing).
"""

from .tokenizer import Token
from .ast_nodes import NumberNode, BinOpNode


class Parser:
    """Parses a list of tokens into an AST.

    Currently does NOT handle operator precedence correctly.
    """

    def __init__(self, tokens):
        self._tokens = tokens
        self._pos = 0

    def parse(self):
        """Parse the token list into an AST.

        Returns:
            An AST node (the root of the expression tree).
        """
        result = self._parse_expression()
        if self._current().type != Token.EOF:
            raise SyntaxError(f"Unexpected token: {self._current()}")
        return result

    def _current(self):
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return Token(Token.EOF, None)

    def _consume(self, expected_type=None, expected_value=None):
        token = self._current()
        if expected_type and token.type != expected_type:
            raise SyntaxError(f"Expected {expected_type}, got {token}")
        if expected_value and token.value != expected_value:
            raise SyntaxError(f"Expected {expected_value!r}, got {token.value!r}")
        self._pos += 1
        return token

    def _parse_expression(self):
        """Parse an expression — BROKEN: no precedence, just left-to-right."""
        left = self._parse_atom()

        while (self._current().type == Token.OPERATOR
               and self._current().value in ('+', '-', '*', '/')):
            op = self._consume().value
            right = self._parse_atom()
            left = BinOpNode(op, left, right)

        return left

    def _parse_atom(self):
        """Parse a number."""
        token = self._current()
        if token.type == Token.NUMBER:
            self._consume()
            return NumberNode(token.value)
        raise SyntaxError(f"Unexpected token: {token}")
