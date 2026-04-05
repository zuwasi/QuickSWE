import subprocess
import os
import pytest

SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "src")
BINARY = os.path.join(SRC_DIR, "tokenizer")
if os.name == "nt":
    BINARY += ".exe"


def compile_cpp():
    result = subprocess.run(
        ["g++", "-std=c++17", "-o", BINARY,
         os.path.join(SRC_DIR, "main.cpp")],
        capture_output=True, text=True
    )
    assert result.returncode == 0, f"Compilation failed:\n{result.stderr}"


def run_binary(test_name):
    compile_cpp()
    result = subprocess.run(
        [BINARY, test_name],
        capture_output=True, text=True, timeout=10
    )
    return result.stdout.strip()


# ── fail_to_pass ────────────────────────────────────────────────────────────

@pytest.mark.fail_to_pass
def test_trailing_escape():
    output = run_binary("test_trailing_escape")
    assert "PASS: test_trailing_escape" in output


@pytest.mark.fail_to_pass
def test_roundtrip():
    output = run_binary("test_roundtrip")
    assert "PASS: test_roundtrip" in output


# ── pass_to_pass ────────────────────────────────────────────────────────────

def test_basic_split():
    output = run_binary("test_basic_split")
    assert "PASS: test_basic_split" in output


def test_escaped_delimiter():
    output = run_binary("test_escaped_delimiter")
    assert "PASS: test_escaped_delimiter" in output


def test_escaped_backslash_before_delim():
    output = run_binary("test_escaped_backslash_before_delim")
    assert "PASS: test_escaped_backslash_before_delim" in output


def test_empty_tokens():
    output = run_binary("test_empty_tokens")
    assert "PASS: test_empty_tokens" in output
