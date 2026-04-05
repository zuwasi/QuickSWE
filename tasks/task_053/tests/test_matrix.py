import subprocess
import os
import pytest

SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "src")
BINARY = os.path.join(SRC_DIR, "matrix")
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
def test_rect_multiply():
    output = run_binary("test_rect_multiply")
    assert "PASS: test_rect_multiply" in output


@pytest.mark.fail_to_pass
def test_identity_property():
    output = run_binary("test_identity_property")
    assert "PASS: test_identity_property" in output


@pytest.mark.fail_to_pass
def test_transpose_product():
    output = run_binary("test_transpose_product")
    assert "PASS: test_transpose_product" in output


# ── pass_to_pass ────────────────────────────────────────────────────────────

def test_transpose_basic():
    output = run_binary("test_transpose_basic")
    assert "PASS: test_transpose_basic" in output


def test_result_dimensions():
    output = run_binary("test_result_dimensions")
    assert "PASS: test_result_dimensions" in output
