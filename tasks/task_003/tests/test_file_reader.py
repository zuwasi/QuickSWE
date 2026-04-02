import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.file_reader import read_text_file


# ---------------------------------------------------------------------------
# fail_to_pass: these tests expose the wrong default encoding
# ---------------------------------------------------------------------------

@pytest.mark.fail_to_pass
def test_default_encoding_reads_utf8():
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", encoding="utf-8", delete=False
    ) as f:
        f.write("café au lait")
        path = f.name
    try:
        content = read_text_file(path)  # encoding=None -> should use utf-8
        assert content == "café au lait"
    finally:
        os.unlink(path)


@pytest.mark.fail_to_pass
def test_default_encoding_reads_unicode_symbols():
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", encoding="utf-8", delete=False
    ) as f:
        f.write("naïve über résumé")
        path = f.name
    try:
        content = read_text_file(path)
        assert content == "naïve über résumé"
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# pass_to_pass: regression tests that already pass with the buggy code
# ---------------------------------------------------------------------------

def test_read_ascii_file():
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", encoding="ascii", delete=False
    ) as f:
        f.write("hello world")
        path = f.name
    try:
        content = read_text_file(path)
        assert content == "hello world"
    finally:
        os.unlink(path)


def test_explicit_utf8_encoding():
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", encoding="utf-8", delete=False
    ) as f:
        f.write("café")
        path = f.name
    try:
        content = read_text_file(path, encoding="utf-8")
        assert content == "café"
    finally:
        os.unlink(path)


def test_file_not_found():
    with pytest.raises(FileNotFoundError):
        read_text_file("/nonexistent/path/file.txt")
