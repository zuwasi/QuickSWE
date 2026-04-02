import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.csv_parser import parse_csv


# ---------------------------------------------------------------------------
# fail_to_pass: these tests expose the bugs
# ---------------------------------------------------------------------------

@pytest.mark.fail_to_pass
def test_empty_string_returns_empty_list():
    assert parse_csv("") == []


@pytest.mark.fail_to_pass
def test_trailing_comma_handled():
    """Row with trailing comma should pad/truncate gracefully, not raise."""
    text = "name,age\nAlice,30,\nBob,25"
    result = parse_csv(text)
    assert len(result) == 2
    assert result[0]["name"] == "Alice"
    assert result[0]["age"] == "30"
    assert result[1] == {"name": "Bob", "age": "25"}


@pytest.mark.fail_to_pass
def test_fewer_fields_than_headers():
    """Row with fewer fields should pad with empty strings, not raise."""
    text = "name,age,city\nAlice,30"
    result = parse_csv(text)
    assert result == [{"name": "Alice", "age": "30", "city": ""}]


# ---------------------------------------------------------------------------
# pass_to_pass: regression tests that already pass with the buggy code
# ---------------------------------------------------------------------------

def test_normal_csv():
    text = "name,age\nAlice,30\nBob,25"
    result = parse_csv(text)
    assert len(result) == 2
    assert result[0] == {"name": "Alice", "age": "30"}
    assert result[1] == {"name": "Bob", "age": "25"}


def test_single_column():
    text = "name\nAlice\nBob"
    result = parse_csv(text)
    assert result == [{"name": "Alice"}, {"name": "Bob"}]


def test_header_only():
    text = "name,age"
    result = parse_csv(text)
    assert result == []


def test_whitespace_lines_skipped():
    text = "name\nAlice\n  \nBob"
    result = parse_csv(text)
    assert result == [{"name": "Alice"}, {"name": "Bob"}]
