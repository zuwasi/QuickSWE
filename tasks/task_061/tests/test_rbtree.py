import subprocess
import os
import pytest

SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "src")
BINARY = os.path.join(SRC_DIR, "rbtree")
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
def test_sorted_insert_valid():
    output = run_binary("test_sorted_insert_valid")
    assert "PASS: test_sorted_insert_valid" in output


@pytest.mark.fail_to_pass
def test_reverse_insert_valid():
    output = run_binary("test_reverse_insert_valid")
    assert "PASS: test_reverse_insert_valid" in output


@pytest.mark.fail_to_pass
def test_height_logarithmic():
    output = run_binary("test_height_logarithmic")
    assert "PASS: test_height_logarithmic" in output


@pytest.mark.fail_to_pass
def test_large_valid():
    output = run_binary("test_large_valid")
    assert "PASS: test_large_valid" in output


# ── pass_to_pass ────────────────────────────────────────────────────────────

def test_inorder_sorted():
    output = run_binary("test_inorder_sorted")
    assert "PASS: test_inorder_sorted" in output


def test_search():
    output = run_binary("test_search")
    assert "PASS: test_search" in output
