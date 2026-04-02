import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.document import Document
from src.diff import DiffEngine, DiffOp, OpType
from src.patch import PatchEngine, PatchError


# ── pass-to-pass: Document basic operations ──────────────────────────


class TestDocumentBasic:
    def test_create_from_string(self):
        doc = Document("hello\nworld")
        assert doc.line_count == 2
        assert doc.get_line(0) == "hello"
        assert doc.get_line(1) == "world"

    def test_create_empty(self):
        doc = Document()
        assert doc.is_empty()
        assert doc.line_count == 0

    def test_from_lines(self):
        doc = Document.from_lines(["a", "b", "c"])
        assert doc.lines == ["a", "b", "c"]

    def test_content_property(self):
        doc = Document("line1\nline2\nline3")
        assert doc.content == "line1\nline2\nline3"

    def test_equality(self):
        doc1 = Document("abc\ndef")
        doc2 = Document("abc\ndef")
        assert doc1 == doc2

    def test_inequality(self):
        doc1 = Document("abc")
        doc2 = Document("xyz")
        assert doc1 != doc2

    def test_get_line_out_of_range(self):
        doc = Document("only one line")
        with pytest.raises(IndexError):
            doc.get_line(5)


# ── fail-to-pass: DiffEngine compute_diff ──────────────────────────


class TestDiffEngineComputeDiff:
    @pytest.mark.fail_to_pass
    def test_identical_documents_all_keep(self):
        """Diffing identical docs should produce only KEEP ops."""
        doc = Document("alpha\nbeta\ngamma")
        engine = DiffEngine()
        ops = engine.compute_diff(doc, doc)
        assert all(op.op == OpType.KEEP for op in ops)
        assert len(ops) == 3

    @pytest.mark.fail_to_pass
    def test_empty_to_content(self):
        """Diffing empty -> content should produce only ADD ops."""
        doc_a = Document()
        doc_b = Document("hello\nworld")
        engine = DiffEngine()
        ops = engine.compute_diff(doc_a, doc_b)
        assert all(op.op == OpType.ADD for op in ops)
        assert len(ops) == 2

    @pytest.mark.fail_to_pass
    def test_content_to_empty(self):
        """Diffing content -> empty should produce only REMOVE ops."""
        doc_a = Document("hello\nworld")
        doc_b = Document()
        engine = DiffEngine()
        ops = engine.compute_diff(doc_a, doc_b)
        assert all(op.op == OpType.REMOVE for op in ops)
        assert len(ops) == 2

    @pytest.mark.fail_to_pass
    def test_both_empty(self):
        """Diffing two empty docs should produce no ops."""
        engine = DiffEngine()
        ops = engine.compute_diff(Document(), Document())
        assert ops == []

    @pytest.mark.fail_to_pass
    def test_add_lines_in_middle(self):
        """Inserting lines in the middle produces correct ops."""
        doc_a = Document("a\nc")
        doc_b = Document("a\nb\nc")
        engine = DiffEngine()
        ops = engine.compute_diff(doc_a, doc_b)
        keep_ops = [op for op in ops if op.op == OpType.KEEP]
        add_ops = [op for op in ops if op.op == OpType.ADD]
        assert len(keep_ops) == 2  # 'a' and 'c' kept
        assert len(add_ops) == 1  # 'b' added
        assert add_ops[0].line == "b"

    @pytest.mark.fail_to_pass
    def test_remove_line(self):
        """Removing a line produces a REMOVE op."""
        doc_a = Document("a\nb\nc")
        doc_b = Document("a\nc")
        engine = DiffEngine()
        ops = engine.compute_diff(doc_a, doc_b)
        remove_ops = [op for op in ops if op.op == OpType.REMOVE]
        assert len(remove_ops) == 1
        assert remove_ops[0].line == "b"

    @pytest.mark.fail_to_pass
    def test_replace_line(self):
        """Changing a line produces REMOVE + ADD."""
        doc_a = Document("a\nb\nc")
        doc_b = Document("a\nB\nc")
        engine = DiffEngine()
        ops = engine.compute_diff(doc_a, doc_b)
        remove_ops = [op for op in ops if op.op == OpType.REMOVE]
        add_ops = [op for op in ops if op.op == OpType.ADD]
        assert len(remove_ops) == 1
        assert remove_ops[0].line == "b"
        assert len(add_ops) == 1
        assert add_ops[0].line == "B"


# ── fail-to-pass: PatchEngine apply_patch ──────────────────────────


class TestPatchEngineApply:
    @pytest.mark.fail_to_pass
    def test_apply_patch_produces_target(self):
        """apply_patch(A, diff(A,B)) == B."""
        doc_a = Document("line1\nline2\nline3")
        doc_b = Document("line1\nmodified\nline3\nline4")
        diff_eng = DiffEngine()
        patch_eng = PatchEngine()
        ops = diff_eng.compute_diff(doc_a, doc_b)
        result = patch_eng.apply_patch(doc_a, ops)
        assert result == doc_b

    @pytest.mark.fail_to_pass
    def test_apply_patch_empty_to_content(self):
        """Patching empty doc with add-only diff produces content."""
        doc_a = Document()
        doc_b = Document("new\ncontent")
        diff_eng = DiffEngine()
        patch_eng = PatchEngine()
        ops = diff_eng.compute_diff(doc_a, doc_b)
        result = patch_eng.apply_patch(doc_a, ops)
        assert result == doc_b

    @pytest.mark.fail_to_pass
    def test_apply_empty_diff(self):
        """Applying an empty diff returns same document."""
        doc = Document("unchanged")
        patch_eng = PatchEngine()
        result = patch_eng.apply_patch(doc, [])
        assert result == doc


# ── fail-to-pass: PatchEngine reverse_patch ──────────────────────────


class TestPatchEngineReverse:
    @pytest.mark.fail_to_pass
    def test_reverse_patch_restores_original(self):
        """reverse_patch(B, diff(A,B)) == A."""
        doc_a = Document("alpha\nbeta\ngamma")
        doc_b = Document("alpha\nBETA\ngamma\ndelta")
        diff_eng = DiffEngine()
        patch_eng = PatchEngine()
        ops = diff_eng.compute_diff(doc_a, doc_b)
        result = patch_eng.reverse_patch(doc_b, ops)
        assert result == doc_a

    @pytest.mark.fail_to_pass
    def test_reverse_patch_content_to_empty(self):
        """Reversing a diff that added all content should produce empty doc."""
        doc_a = Document()
        doc_b = Document("new\nstuff")
        diff_eng = DiffEngine()
        patch_eng = PatchEngine()
        ops = diff_eng.compute_diff(doc_a, doc_b)
        result = patch_eng.reverse_patch(doc_b, ops)
        assert result == doc_a

    @pytest.mark.fail_to_pass
    def test_roundtrip_complex(self):
        """Full roundtrip: A -> diff -> patch -> B -> reverse -> A."""
        doc_a = Document("first\nsecond\nthird\nfourth\nfifth")
        doc_b = Document("first\nSECOND\nthird\nextra\nfifth\nsixth")
        diff_eng = DiffEngine()
        patch_eng = PatchEngine()
        ops = diff_eng.compute_diff(doc_a, doc_b)
        patched = patch_eng.apply_patch(doc_a, ops)
        assert patched == doc_b
        reversed_doc = patch_eng.reverse_patch(patched, ops)
        assert reversed_doc == doc_a
