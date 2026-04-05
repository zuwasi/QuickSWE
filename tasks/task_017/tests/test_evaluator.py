import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.evaluator import evaluate, evaluate_safe, tokenize, format_result


# ─── fail_to_pass ───────────────────────────────────────────────

@pytest.mark.fail_to_pass
def test_multiply_before_add():
    """3 + 4 * 2 must equal 11, not 14."""
    assert evaluate("3 + 4 * 2") == 11


@pytest.mark.fail_to_pass
def test_divide_before_subtract():
    """10 - 6 / 2 must equal 7, not 2."""
    assert evaluate("10 - 6 / 2") == 7


@pytest.mark.fail_to_pass
def test_mixed_precedence():
    """2 + 3 * 4 - 1 must equal 13."""
    result = evaluate("2 + 3 * 4 - 1")
    assert result == 13, f"Expected 13, got {result}"


@pytest.mark.fail_to_pass
def test_complex_precedence():
    """1 + 2 * 3 + 4 * 5 must equal 27."""
    result = evaluate("1 + 2 * 3 + 4 * 5")
    assert result == 27, f"Expected 27, got {result}"


# ─── pass_to_pass ───────────────────────────────────────────────

def test_simple_addition():
    """2 + 3 = 5."""
    assert evaluate("2 + 3") == 5


def test_parenthesised_expression():
    """(3 + 4) * 2 = 14."""
    assert evaluate("(3 + 4) * 2") == 14


def test_negative_number():
    """-5 + 3 = -2."""
    assert evaluate("-5 + 3") == -2
