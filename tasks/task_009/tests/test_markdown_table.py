import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.markdown_table import parse_table


# ──────────────────────────────────────────────
# pass_to_pass: these must always pass
# ──────────────────────────────────────────────


class TestMarkdownTableBasics:
    """Tests for basic table parsing that already works."""

    def test_simple_table(self):
        text = """\
| Name  | Age |
|-------|-----|
| Alice | 30  |
| Bob   | 25  |"""
        result = parse_table(text)
        assert len(result) == 2
        assert result[0]["Name"] == "Alice"
        assert result[1]["Age"] == "25"

    def test_single_row(self):
        text = """\
| X | Y |
|---|---|
| 1 | 2 |"""
        result = parse_table(text)
        assert len(result) == 1
        assert result[0] == {"X": "1", "Y": "2"}

    def test_extra_whitespace(self):
        text = """\
|  Name   |  Score  |
|---------|---------|
|  Carol  |  95     |"""
        result = parse_table(text)
        assert result[0]["Name"] == "Carol"
        assert result[0]["Score"] == "95"


# ──────────────────────────────────────────────
# fail_to_pass: these fail before the fix
# ──────────────────────────────────────────────


class TestEscapedPipes:
    r"""Tests for escaped pipe handling in cell content (\|)."""

    @pytest.mark.fail_to_pass
    def test_escaped_pipe_in_cell(self):
        r"""Cell containing \| should have a literal pipe in the parsed value."""
        text = (
            "| Expression | Result |\n"
            "|------------|--------|\n"
            "| A \\| B     | true   |"
        )
        result = parse_table(text)
        assert len(result) == 1
        assert result[0]["Expression"] == "A | B"
        assert result[0]["Result"] == "true"

    @pytest.mark.fail_to_pass
    def test_multiple_escaped_pipes(self):
        r"""Multiple \| in the same row."""
        text = (
            "| Col1       | Col2       |\n"
            "|------------|------------|\n"
            "| x \\| y     | a \\| b     |"
        )
        result = parse_table(text)
        assert result[0]["Col1"] == "x | y"
        assert result[0]["Col2"] == "a | b"

    @pytest.mark.fail_to_pass
    def test_escaped_pipe_in_header(self):
        r"""Headers can also contain \|."""
        text = (
            "| A \\| B | C |\n"
            "|--------|---|\n"
            "| val1   | 2 |"
        )
        result = parse_table(text)
        assert "A | B" in result[0]
        assert result[0]["A | B"] == "val1"
