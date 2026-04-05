import subprocess
import os
import pytest

SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "src")
BINARY = os.path.join(SRC_DIR, "min_heap")
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
def test_descending_insert():
    output = run_binary("test_descending_insert")
    assert "PASS: test_descending_insert" in output


@pytest.mark.fail_to_pass
def test_large_heap():
    output = run_binary("test_large_heap")
    assert "PASS: test_large_heap" in output


# ── pass_to_pass ────────────────────────────────────────────────────────────

def test_basic_push_pop():
    output = run_binary("test_basic_push_pop")
    assert "PASS: test_basic_push_pop" in output


def test_single_element():
    output = run_binary("test_single_element")
    assert "PASS: test_single_element" in output


def test_duplicates():
    output = run_binary("test_duplicates")
    assert "PASS: test_duplicates" in output


def test_interleaved():
    output = run_binary("test_interleaved")
    assert "PASS: test_interleaved" in output
