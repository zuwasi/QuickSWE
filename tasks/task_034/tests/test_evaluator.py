"""Tests for the expression evaluator with operator precedence."""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.tokenizer import Tokenizer, Token
from src.parser import Parser
from src.evaluator import Evaluator
from src.formatter import Formatter


def evaluate(expr):
    """Helper: tokenize, parse, and evaluate an expression string."""
    tokens = Tokenizer(expr).tokenize()
    ast = Parser(tokens).parse()
    return Evaluator().evaluate(ast)


def format_expr(expr):
    """Helper: tokenize, parse, and format an expression string."""
    tokens = Tokenizer(expr).tokenize()
    ast = Parser(tokens).parse()
    return Formatter().format(ast)


# ============================================================
# PASS-TO-PASS: Basic arithmetic that currently works
# ============================================================

class TestBasicArithmetic:
    """These should pass with the existing (broken-precedence) code
    because they don't rely on precedence."""

    def test_single_number(self):
        assert evaluate("42") == 42

    def test_float_number(self):
        assert evaluate("3.14") == 3.14

    def test_simple_addition(self):
        assert evaluate("2 + 3") == 5

    def test_simple_subtraction(self):
        assert evaluate("10 - 4") == 6

    def test_simple_multiplication(self):
        assert evaluate("3 * 7") == 21

    def test_simple_division(self):
        assert evaluate("20 / 4") == 5.0

    def test_division_by_zero(self):
        with pytest.raises(ZeroDivisionError):
            evaluate("5 / 0")

    def test_chained_addition(self):
        assert evaluate("1 + 2 + 3") == 6

    def test_chained_subtraction(self):
        assert evaluate("10 - 3 - 2") == 5


class TestBasicFormatter:
    def test_format_number(self):
        assert format_expr("42") == "42"

    def test_format_binop(self):
        result = format_expr("2 + 3")
        assert result == "(2 + 3)"


class TestBasicTokenizer:
    def test_tokens_simple(self):
        tokens = Tokenizer("2 + 3").tokenize()
        assert tokens[0] == Token(Token.NUMBER, 2)
        assert tokens[1] == Token(Token.OPERATOR, '+')
        assert tokens[2] == Token(Token.NUMBER, 3)
        assert tokens[3] == Token(Token.EOF, None)


# ============================================================
# FAIL-TO-PASS: Operator precedence and new operators
# ============================================================

@pytest.mark.fail_to_pass
class TestOperatorPrecedence:
    """These tests FAIL with the current left-to-right parser."""

    def test_multiply_before_add(self):
        assert evaluate("2 + 3 * 4") == 14  # Not 20

    def test_divide_before_subtract(self):
        assert evaluate("10 - 6 / 2") == 7.0  # Not 2

    def test_mixed_precedence(self):
        assert evaluate("1 + 2 * 3 + 4") == 11  # Not 13

    def test_add_then_multiply_then_add(self):
        # 5 + 2 * 3 + 1 = 5 + 6 + 1 = 12
        assert evaluate("5 + 2 * 3 + 1") == 12

    def test_complex_precedence(self):
        assert evaluate("2 + 3 * 4 - 1") == 13  # 2 + 12 - 1

    def test_all_four_ops(self):
        # 10 + 2 * 3 - 8 / 4 = 10 + 6 - 2 = 14
        assert evaluate("10 + 2 * 3 - 8 / 4") == 14.0


@pytest.mark.fail_to_pass
class TestParentheses:
    def test_parens_override_precedence(self):
        assert evaluate("(2 + 3) * 4") == 20

    def test_nested_parens(self):
        assert evaluate("((2 + 3)) * 4") == 20

    def test_complex_parens(self):
        assert evaluate("(1 + 2) * (3 + 4)") == 21

    def test_parens_in_denominator(self):
        assert evaluate("12 / (2 + 1)") == 4.0


@pytest.mark.fail_to_pass
class TestUnaryMinus:
    def test_unary_minus(self):
        assert evaluate("-5") == -5

    def test_unary_minus_in_expr(self):
        assert evaluate("-5 + 3") == -2

    def test_double_unary_minus(self):
        assert evaluate("--5") == 5

    def test_unary_minus_with_parens(self):
        assert evaluate("-(3 + 4)") == -7

    def test_unary_minus_multiply(self):
        assert evaluate("-2 * 3") == -6


@pytest.mark.fail_to_pass
class TestPowerOperator:
    def test_basic_power(self):
        assert evaluate("2 ^ 3") == 8

    def test_power_right_associative(self):
        # 2^3^2 = 2^(3^2) = 2^9 = 512, NOT (2^3)^2 = 64
        assert evaluate("2 ^ 3 ^ 2") == 512

    def test_power_higher_than_multiply(self):
        assert evaluate("2 * 3 ^ 2") == 18  # 2 * 9 = 18

    def test_power_with_parens(self):
        assert evaluate("(2 ^ 3) ^ 2") == 64

    def test_negative_base_power(self):
        assert evaluate("(-2) ^ 3") == -8


@pytest.mark.fail_to_pass
class TestComparisonOperators:
    def test_less_than(self):
        assert evaluate("3 < 5") is True

    def test_greater_than(self):
        assert evaluate("5 > 3") is True

    def test_equals(self):
        assert evaluate("3 == 3") is True

    def test_not_equals(self):
        assert evaluate("3 != 4") is True

    def test_less_equals(self):
        assert evaluate("3 <= 3") is True

    def test_greater_equals(self):
        assert evaluate("4 >= 5") is False

    def test_comparison_with_arithmetic(self):
        assert evaluate("2 + 3 > 4") is True  # 5 > 4

    def test_comparison_false(self):
        assert evaluate("10 < 5") is False


@pytest.mark.fail_to_pass
class TestBooleanOperators:
    def test_and_true(self):
        assert evaluate("true and true") is True

    def test_and_false(self):
        assert evaluate("true and false") is False

    def test_or_true(self):
        assert evaluate("false or true") is True

    def test_or_false(self):
        assert evaluate("false or false") is False

    def test_not_true(self):
        assert evaluate("not true") is False

    def test_not_false(self):
        assert evaluate("not false") is True

    def test_boolean_with_comparison(self):
        assert evaluate("3 > 2 and 5 < 10") is True

    def test_complex_boolean(self):
        assert evaluate("not (3 > 5) and 2 < 4") is True

    def test_boolean_precedence(self):
        # `or` has lower precedence than `and`
        # false and true or true => (false and true) or true => false or true => True
        assert evaluate("false and true or true") is True

    def test_not_precedence(self):
        # not false and true => (not false) and true => True and True => True
        assert evaluate("not false and true") is True


@pytest.mark.fail_to_pass
class TestMixedExpressions:
    """Complex expressions mixing multiple operator types."""

    def test_arithmetic_and_comparison(self):
        # (2 + 3) * 4 > 15 => 20 > 15 => True
        assert evaluate("(2 + 3) * 4 > 15") is True

    def test_nested_boolean_and_arithmetic(self):
        # 2 ^ 3 == 8 and 3 * 3 == 9
        assert evaluate("2 ^ 3 == 8 and 3 * 3 == 9") is True

    def test_unary_in_comparison(self):
        assert evaluate("-3 < 0") is True

    def test_power_in_comparison(self):
        assert evaluate("2 ^ 10 > 1000") is True  # 1024 > 1000

    def test_complex_nested_everything(self):
        # not (2 + 3 > 10) => not (5 > 10) => not False => True
        assert evaluate("not (2 + 3 > 10)") is True

    def test_chained_power_in_expression(self):
        # 1 + 2 ^ 3 = 1 + 8 = 9
        assert evaluate("1 + 2 ^ 3") == 9

    def test_multiple_unary(self):
        assert evaluate("- - - 5") == -5

    def test_boolean_literals_in_expression(self):
        assert evaluate("true") is True
        assert evaluate("false") is False


@pytest.mark.fail_to_pass
class TestFormatterNewOps:
    def test_format_power(self):
        result = format_expr("2 ^ 3")
        assert "^" in result
        assert "2" in result
        assert "3" in result

    def test_format_unary_minus(self):
        result = format_expr("-5")
        assert "-" in result
        assert "5" in result

    def test_format_comparison(self):
        result = format_expr("3 > 2")
        assert ">" in result

    def test_format_boolean(self):
        result = format_expr("true and false")
        assert "and" in result
