import subprocess
import os
import pytest

SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "src")
BINARY = os.path.join(SRC_DIR, "lockfree_stack")
if os.name == "nt":
    BINARY += ".exe"


def compile_cpp():
    result = subprocess.run(
        ["g++", "-std=c++17", "-o", BINARY,
         os.path.join(SRC_DIR, "main.cpp"), "-lpthread"],
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
def test_push_pop_push_sequence():
    output = run_binary("test_push_pop_push_sequence")
    assert "PASS: test_push_pop_push_sequence" in output


@pytest.mark.fail_to_pass
def test_tag_increments_on_push():
    output = run_binary("test_tag_increments_on_push")
    assert "PASS: test_tag_increments_on_push" in output


@pytest.mark.fail_to_pass
def test_drain():
    output = run_binary("test_drain")
    assert "PASS: test_drain" in output


# ── pass_to_pass ────────────────────────────────────────────────────────────

def test_basic_lifo():
    output = run_binary("test_basic_lifo")
    assert "PASS: test_basic_lifo" in output


def test_empty_pop():
    output = run_binary("test_empty_pop")
    assert "PASS: test_empty_pop" in output


def test_size():
    output = run_binary("test_size")
    assert "PASS: test_size" in output
