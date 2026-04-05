import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.lexer import Lexer, TokenType, tokenize, TokenStream


class TestBasicTokenization:
    """Tests that should pass both before and after the fix."""

    @pytest.mark.pass_to_pass
    def test_simple_arithmetic(self):
        tokens = tokenize("a + b * c")
        types = [t.type for t in tokens if t.type != TokenType.EOF]
        assert types == [
            TokenType.IDENTIFIER, TokenType.PLUS,
            TokenType.IDENTIFIER, TokenType.STAR,
            TokenType.IDENTIFIER,
        ]

    @pytest.mark.pass_to_pass
    def test_two_char_operators(self):
        tokens = tokenize("a += b; c == d; e != f")
        types = [t.type for t in tokens if t.type != TokenType.EOF]
        assert types == [
            TokenType.IDENTIFIER, TokenType.PLUS_ASSIGN, TokenType.IDENTIFIER,
            TokenType.SEMICOLON,
            TokenType.IDENTIFIER, TokenType.EQ, TokenType.IDENTIFIER,
            TokenType.SEMICOLON,
            TokenType.IDENTIFIER, TokenType.NEQ, TokenType.IDENTIFIER,
        ]

    @pytest.mark.pass_to_pass
    def test_shift_operators(self):
        tokens = tokenize("x << 2; y >> 3")
        types = [t.type for t in tokens if t.type != TokenType.EOF]
        assert types == [
            TokenType.IDENTIFIER, TokenType.LSHIFT, TokenType.INTEGER,
            TokenType.SEMICOLON,
            TokenType.IDENTIFIER, TokenType.RSHIFT, TokenType.INTEGER,
        ]


class TestThreeCharOperators:
    """Tests that should fail before the fix and pass after."""

    @pytest.mark.fail_to_pass
    def test_right_shift_assign(self):
        tokens = tokenize("x >>= 1;")
        types = [t.type for t in tokens if t.type != TokenType.EOF]
        assert types == [
            TokenType.IDENTIFIER,
            TokenType.RSHIFT_ASSIGN,
            TokenType.INTEGER,
            TokenType.SEMICOLON,
        ]
        assert tokens[1].value == ">>="

    @pytest.mark.fail_to_pass
    def test_left_shift_assign(self):
        tokens = tokenize("y <<= 4;")
        types = [t.type for t in tokens if t.type != TokenType.EOF]
        assert types == [
            TokenType.IDENTIFIER,
            TokenType.LSHIFT_ASSIGN,
            TokenType.INTEGER,
            TokenType.SEMICOLON,
        ]
        assert tokens[1].value == "<<="

    @pytest.mark.fail_to_pass
    def test_ellipsis(self):
        tokens = tokenize("void foo(int a, ...)")
        types = [t.type for t in tokens if t.type != TokenType.EOF]
        assert types == [
            TokenType.VOID, TokenType.IDENTIFIER, TokenType.LPAREN,
            TokenType.INT, TokenType.IDENTIFIER, TokenType.COMMA,
            TokenType.ELLIPSIS,
            TokenType.RPAREN,
        ]
        assert any(t.type == TokenType.ELLIPSIS and t.value == "..." for t in tokens)

    @pytest.mark.fail_to_pass
    def test_mixed_compound_shifts(self):
        tokens = tokenize("a >>= b; c <<= d;")
        types = [t.type for t in tokens if t.type != TokenType.EOF]
        assert types == [
            TokenType.IDENTIFIER, TokenType.RSHIFT_ASSIGN, TokenType.IDENTIFIER,
            TokenType.SEMICOLON,
            TokenType.IDENTIFIER, TokenType.LSHIFT_ASSIGN, TokenType.IDENTIFIER,
            TokenType.SEMICOLON,
        ]
