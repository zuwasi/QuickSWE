import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.regex_engine import regex_match, regex_search, regex_find_all


class TestRegexPassToPass:
    """Tests that should pass both before and after the fix."""

    def test_literal_match(self):
        assert regex_search("abc", "xyzabcdef")

    def test_dot_matches_any(self):
        assert regex_search("a.c", "axc")
        assert not regex_search("a.c", "ac")

    def test_star_zero_or_more(self):
        assert regex_search("ab*c", "ac")
        assert regex_search("ab*c", "abbc")


@pytest.mark.fail_to_pass
class TestRegexFailToPass:
    """Tests that fail before the fix and pass after."""

    def test_star_group_plus_no_hang(self):
        result = regex_match("(a*)+b", "aaab", timeout=50000)
        assert result is not None
        s, e = result
        assert s == 0 and e == 4

    def test_nested_star_plus_on_empty(self):
        result = regex_match("(x*)+y", "y", timeout=50000)
        assert result is not None

    def test_optional_group_plus(self):
        result = regex_match("([ab]*)+c", "ababc", timeout=50000)
        assert result is not None
        s, e = result
        assert e == 5
