"""Arithmetic expression evaluator with tokenizer and parser."""

from typing import List, Optional, Union


class TokenType:
    NUMBER = "NUMBER"
    PLUS = "PLUS"
    MINUS = "MINUS"
    MULTIPLY = "MULTIPLY"
    DIVIDE = "DIVIDE"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    EOF = "EOF"


class Token:
    """Represents a single token in the expression."""

    def __init__(self, type_: str, value: Union[str, float]):
        self.type = type_
        self.value = value

    def __repr__(self):
        return f"Token({self.type}, {self.value!r})"


def tokenize(expression: str) -> List[Token]:
    """Convert an expression string into a list of tokens."""
    tokens = []
    i = 0
    while i < len(expression):
        ch = expression[i]

        if ch.isspace():
            i += 1
            continue

        if ch.isdigit() or ch == ".":
            start = i
            has_dot = ch == "."
            i += 1
            while i < len(expression) and (expression[i].isdigit() or
                                            (expression[i] == "." and not has_dot)):
                if expression[i] == ".":
                    has_dot = True
                i += 1
            tokens.append(Token(TokenType.NUMBER, float(expression[start:i])))
            continue

        op_map = {
            "+": TokenType.PLUS,
            "-": TokenType.MINUS,
            "*": TokenType.MULTIPLY,
            "/": TokenType.DIVIDE,
            "(": TokenType.LPAREN,
            ")": TokenType.RPAREN,
        }

        if ch in op_map:
            tokens.append(Token(op_map[ch], ch))
            i += 1
        else:
            raise ValueError(f"Unexpected character: {ch!r} at position {i}")

    tokens.append(Token(TokenType.EOF, ""))
    return tokens


def evaluate(expression: str) -> float:
    """Evaluate an arithmetic expression string and return the result.

    Supports +, -, *, / and parentheses.
    """
    tokens = tokenize(expression)
    result = _parse_expression(tokens)
    return result


def _parse_expression(tokens: List[Token]) -> float:
    """Parse and evaluate an expression from a token list."""
    pos = 0

    def current() -> Token:
        nonlocal pos
        if pos < len(tokens):
            return tokens[pos]
        return Token(TokenType.EOF, "")

    def eat(expected_type: Optional[str] = None) -> Token:
        nonlocal pos
        tok = current()
        if expected_type and tok.type != expected_type:
            raise ValueError(f"Expected {expected_type}, got {tok.type}")
        pos += 1
        return tok

    def parse_primary() -> float:
        tok = current()
        if tok.type == TokenType.NUMBER:
            eat()
            return tok.value
        if tok.type == TokenType.LPAREN:
            eat(TokenType.LPAREN)
            val = parse_expr()
            eat(TokenType.RPAREN)
            return val
        if tok.type == TokenType.MINUS:
            eat()
            return -parse_primary()
        raise ValueError(f"Unexpected token: {tok}")

    def parse_expr() -> float:
        left = parse_primary()

        while current().type in (TokenType.PLUS, TokenType.MINUS,
                                 TokenType.MULTIPLY, TokenType.DIVIDE):
            op = eat()
            right = parse_primary()

            if op.type == TokenType.PLUS:
                left = left + right
            elif op.type == TokenType.MINUS:
                left = left - right
            elif op.type == TokenType.MULTIPLY:
                left = left * right
            elif op.type == TokenType.DIVIDE:
                if right == 0:
                    raise ZeroDivisionError("Division by zero")
                left = left / right

        return left

    return parse_expr()


def evaluate_safe(expression: str) -> Optional[float]:
    """Evaluate an expression, returning None on any error."""
    try:
        return evaluate(expression)
    except Exception:
        return None


def format_result(value: float, precision: int = 6) -> str:
    """Format a numeric result with the given precision."""
    if value == int(value):
        return str(int(value))
    return f"{value:.{precision}f}".rstrip("0").rstrip(".")
