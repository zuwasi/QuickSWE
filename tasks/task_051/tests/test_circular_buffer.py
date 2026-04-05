import subprocess
import os
import pytest

SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "src")
BINARY = os.path.join(SRC_DIR, "circular_buffer")
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
def test_size_after_wrap():
    output = run_binary("test_size_after_wrap")
    assert "PASS: test_size_after_wrap" in output


@pytest.mark.fail_to_pass
def test_overwrite_oldest():
    output = run_binary("test_overwrite_oldest")
    assert "PASS: test_overwrite_oldest" in output


@pytest.mark.fail_to_pass
def test_to_vector_wrapped():
    output = run_binary("test_to_vector_wrapped")
    assert "PASS: test_to_vector_wrapped" in output


# ── pass_to_pass ────────────────────────────────────────────────────────────

def test_basic_push_pop():
    output = run_binary("test_basic_push_pop")
    assert "PASS: test_basic_push_pop" in output


def test_empty_after_drain():
    output = run_binary("test_empty_after_drain")
    assert "PASS: test_empty_after_drain" in output


def test_single_element():
    output = run_binary("test_single_element")
    assert "PASS: test_single_element" in output
