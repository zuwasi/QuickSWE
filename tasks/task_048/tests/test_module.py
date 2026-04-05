import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.incremental_parser import (
    IncrementalParser, NodeKind, collect_statements, count_nodes,
)


class TestBasicParsing:
    """Tests that should pass both before and after the fix."""

    @pytest.mark.pass_to_pass
    def test_parse_assignment(self):
        p = IncrementalParser()
        ast = p.parse("x = 42;")
        stmts = collect_statements(ast)
        assert len(stmts) == 1
        assert stmts[0].kind == NodeKind.ASSIGNMENT
        assert stmts[0].value == "x"

    @pytest.mark.pass_to_pass
    def test_parse_expression(self):
        p = IncrementalParser()
        ast = p.parse("1 + 2 * 3;")
        stmts = collect_statements(ast)
        assert len(stmts) == 1
        assert stmts[0].kind == NodeKind.EXPR_STMT

    @pytest.mark.pass_to_pass
    def test_parse_multiple_statements(self):
        p = IncrementalParser()
        ast = p.parse("x = 1; y = 2; z = 3;")
        stmts = collect_statements(ast)
        assert len(stmts) == 3


class TestErrorRecovery:
    """Tests that should fail before the fix and pass after."""

    @pytest.mark.fail_to_pass
    def test_error_preserves_prior_statements(self):
        """Statements parsed before an error should be preserved in the AST."""
        p = IncrementalParser()
        ast = p.parse("x = 1; y = @@; z = 3;")
        stmts = collect_statements(ast)

        valid_stmts = [s for s in stmts if s.kind != NodeKind.ERROR_NODE]
        assert len(valid_stmts) >= 2, (
            f"Expected at least 2 valid statements (x=1 and z=3), "
            f"got {len(valid_stmts)}: {[s.kind.name for s in stmts]}"
        )

        # First statement should be x=1
        assert any(s.kind == NodeKind.ASSIGNMENT and s.value == "x" for s in valid_stmts), (
            "Statement 'x = 1' should be preserved before error"
        )

    @pytest.mark.fail_to_pass
    def test_error_in_middle_keeps_first(self):
        """First valid statement should survive error recovery."""
        p = IncrementalParser()
        ast = p.parse("a = 10; !!!; b = 20;")
        stmts = collect_statements(ast)

        has_a = any(s.kind == NodeKind.ASSIGNMENT and s.value == "a" for s in stmts)
        assert has_a, (
            f"Statement 'a = 10' lost after error recovery. "
            f"Got: {[(s.kind.name, s.value) for s in stmts]}"
        )

    @pytest.mark.fail_to_pass
    def test_multiple_errors_preserve_valid(self):
        """Multiple errors should still preserve all valid statements around them."""
        p = IncrementalParser()
        ast = p.parse("a = 1; @@@; b = 2; $$$; c = 3;")
        stmts = collect_statements(ast)

        valid_names = [s.value for s in stmts if s.kind == NodeKind.ASSIGNMENT]
        assert "a" in valid_names, f"Statement 'a' lost. Valid: {valid_names}"
        assert "b" in valid_names, f"Statement 'b' lost. Valid: {valid_names}"

    @pytest.mark.fail_to_pass
    def test_error_recovery_continues_parsing(self):
        """Parser should continue and parse statements after error."""
        p = IncrementalParser()
        ast = p.parse("x = 1; ??? ; y = 2;")
        stmts = collect_statements(ast)

        has_y = any(s.kind == NodeKind.ASSIGNMENT and s.value == "y" for s in stmts)
        has_x = any(s.kind == NodeKind.ASSIGNMENT and s.value == "x" for s in stmts)
        assert has_x and has_y, (
            f"Both x and y should be in AST. Got: {[(s.kind.name, s.value) for s in stmts]}"
        )
