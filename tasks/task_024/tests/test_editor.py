import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.document import Document
from src.editor import Editor


# ── pass-to-pass: basic document operations ──────────────────────────

class TestDocument:
    def test_empty_document(self):
        doc = Document()
        assert doc.content == ""
        assert len(doc) == 0

    def test_document_with_initial_content(self):
        doc = Document("hello")
        assert doc.content == "hello"
        assert len(doc) == 5

    def test_insert_at_beginning(self):
        doc = Document("world")
        doc.insert(0, "hello ")
        assert doc.content == "hello world"

    def test_insert_at_end(self):
        doc = Document("hello")
        doc.insert(5, " world")
        assert doc.content == "hello world"

    def test_insert_in_middle(self):
        doc = Document("helo")
        doc.insert(2, "l")
        assert doc.content == "hello"

    def test_insert_clamped_position(self):
        doc = Document("abc")
        doc.insert(100, "d")
        assert doc.content == "abcd"
        doc.insert(-5, "z")
        assert doc.content == "zabcd"

    def test_delete_returns_text(self):
        doc = Document("hello world")
        deleted = doc.delete(5, 6)
        assert deleted == " world"
        assert doc.content == "hello"

    def test_delete_clamped(self):
        doc = Document("abc")
        deleted = doc.delete(1, 100)
        assert deleted == "bc"
        assert doc.content == "a"

    def test_get_text_slice(self):
        doc = Document("hello world")
        assert doc.get_text(0, 5) == "hello"
        assert doc.get_text(6) == "world"

    def test_name_property(self):
        doc = Document()
        assert doc.name == "Untitled"
        doc.name = "test.txt"
        assert doc.name == "test.txt"


class TestEditorBasics:
    def test_insert_and_read(self):
        editor = Editor()
        editor.insert(0, "hello")
        assert editor.text == "hello"

    def test_delete_and_read(self):
        editor = Editor(Document("hello world"))
        deleted = editor.delete(5, 6)
        assert deleted == " world"
        assert editor.text == "hello"

    def test_append(self):
        editor = Editor(Document("hello"))
        editor.append(" world")
        assert editor.text == "hello world"

    def test_replace(self):
        editor = Editor(Document("hello world"))
        old = editor.replace(6, 5, "Python")
        assert old == "world"
        assert editor.text == "hello Python"

    def test_clear(self):
        editor = Editor(Document("stuff"))
        old = editor.clear()
        assert old == "stuff"
        assert editor.text == ""

    def test_find(self):
        editor = Editor(Document("hello world"))
        assert editor.find("world") == 6
        assert editor.find("xyz") == -1

    def test_word_count(self):
        editor = Editor(Document("one two three"))
        assert editor.word_count() == 3

    def test_word_count_empty(self):
        editor = Editor(Document(""))
        assert editor.word_count() == 0

    def test_multiple_edits(self):
        editor = Editor()
        editor.insert(0, "AC")
        editor.insert(1, "B")
        assert editor.text == "ABC"
        editor.delete(1, 1)
        assert editor.text == "AC"


# ── fail-to-pass: undo/redo system ──────────────────────────────────

class TestUndoBasic:
    @pytest.mark.fail_to_pass
    def test_undo_insert(self):
        editor = Editor()
        editor.insert(0, "hello")
        assert editor.text == "hello"
        editor.undo()
        assert editor.text == ""

    @pytest.mark.fail_to_pass
    def test_undo_delete(self):
        editor = Editor(Document("hello world"))
        editor.delete(5, 6)
        assert editor.text == "hello"
        editor.undo()
        assert editor.text == "hello world"

    @pytest.mark.fail_to_pass
    def test_undo_append(self):
        editor = Editor(Document("start"))
        editor.append(" end")
        assert editor.text == "start end"
        editor.undo()
        assert editor.text == "start"

    @pytest.mark.fail_to_pass
    def test_multiple_undos(self):
        editor = Editor()
        editor.insert(0, "A")
        editor.insert(1, "B")
        editor.insert(2, "C")
        assert editor.text == "ABC"
        editor.undo()
        assert editor.text == "AB"
        editor.undo()
        assert editor.text == "A"
        editor.undo()
        assert editor.text == ""

    @pytest.mark.fail_to_pass
    def test_undo_on_empty_history_is_noop(self):
        editor = Editor(Document("safe"))
        editor.undo()  # should not crash or change anything
        assert editor.text == "safe"


class TestRedoBasic:
    @pytest.mark.fail_to_pass
    def test_redo_after_undo(self):
        editor = Editor()
        editor.insert(0, "hello")
        editor.undo()
        assert editor.text == ""
        editor.redo()
        assert editor.text == "hello"

    @pytest.mark.fail_to_pass
    def test_multiple_redo(self):
        editor = Editor()
        editor.insert(0, "A")
        editor.insert(1, "B")
        editor.insert(2, "C")
        editor.undo()
        editor.undo()
        editor.undo()
        assert editor.text == ""
        editor.redo()
        assert editor.text == "A"
        editor.redo()
        assert editor.text == "AB"
        editor.redo()
        assert editor.text == "ABC"

    @pytest.mark.fail_to_pass
    def test_redo_cleared_on_new_edit(self):
        editor = Editor()
        editor.insert(0, "hello")
        editor.undo()
        assert editor.text == ""
        # New edit should clear redo stack
        editor.insert(0, "world")
        editor.redo()  # should be a no-op
        assert editor.text == "world"

    @pytest.mark.fail_to_pass
    def test_redo_on_empty_stack_is_noop(self):
        editor = Editor(Document("safe"))
        editor.redo()  # should not crash
        assert editor.text == "safe"


class TestUndoReplace:
    @pytest.mark.fail_to_pass
    def test_undo_replace(self):
        editor = Editor(Document("hello world"))
        editor.replace(6, 5, "Python")
        assert editor.text == "hello Python"
        editor.undo()
        assert editor.text == "hello world"

    @pytest.mark.fail_to_pass
    def test_redo_replace(self):
        editor = Editor(Document("hello world"))
        editor.replace(6, 5, "Python")
        editor.undo()
        assert editor.text == "hello world"
        editor.redo()
        assert editor.text == "hello Python"


class TestTransactions:
    @pytest.mark.fail_to_pass
    def test_transaction_undoes_as_one(self):
        editor = Editor()
        editor.begin_transaction()
        editor.insert(0, "Hello")
        editor.insert(5, " World")
        editor.end_transaction()
        assert editor.text == "Hello World"
        editor.undo()  # should undo both inserts
        assert editor.text == ""

    @pytest.mark.fail_to_pass
    def test_transaction_redoes_as_one(self):
        editor = Editor()
        editor.begin_transaction()
        editor.insert(0, "AB")
        editor.insert(2, "CD")
        editor.end_transaction()
        editor.undo()
        assert editor.text == ""
        editor.redo()  # should redo both
        assert editor.text == "ABCD"

    @pytest.mark.fail_to_pass
    def test_mixed_transaction_and_single(self):
        editor = Editor()
        editor.insert(0, "Start")  # single command
        editor.begin_transaction()
        editor.append(" Middle")
        editor.append(" End")
        editor.end_transaction()
        assert editor.text == "Start Middle End"
        editor.undo()  # undoes the transaction (both appends)
        assert editor.text == "Start"
        editor.undo()  # undoes the first insert
        assert editor.text == ""

    @pytest.mark.fail_to_pass
    def test_transaction_with_delete_and_insert(self):
        editor = Editor(Document("ABCDEF"))
        editor.begin_transaction()
        editor.delete(3, 3)   # remove "DEF"
        editor.insert(3, "XYZ")  # add "XYZ"
        editor.end_transaction()
        assert editor.text == "ABCXYZ"
        editor.undo()
        assert editor.text == "ABCDEF"
