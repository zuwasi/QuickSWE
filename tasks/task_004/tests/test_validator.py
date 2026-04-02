import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.validator import validate_email


# ---------------------------------------------------------------------------
# fail_to_pass: these tests expose the overly restrictive regex
# ---------------------------------------------------------------------------

@pytest.mark.fail_to_pass
def test_dot_in_local_part():
    assert validate_email("user.name@example.com") is True


@pytest.mark.fail_to_pass
def test_hyphen_in_domain():
    assert validate_email("test@my-domain.com") is True


@pytest.mark.fail_to_pass
def test_subdomain_with_hyphen():
    assert validate_email("test@my-domain.co.uk") is True


@pytest.mark.fail_to_pass
def test_multiple_dots_in_local():
    assert validate_email("first.middle.last@example.com") is True


# ---------------------------------------------------------------------------
# pass_to_pass: regression tests that already pass with the buggy code
# ---------------------------------------------------------------------------

def test_simple_valid_email():
    assert validate_email("user@example.com") is True


def test_no_at_sign():
    assert validate_email("userexample.com") is False


def test_no_domain():
    assert validate_email("user@") is False


def test_no_local_part():
    assert validate_email("@example.com") is False


def test_empty_string():
    assert validate_email("") is False


def test_spaces():
    assert validate_email("user @example.com") is False
