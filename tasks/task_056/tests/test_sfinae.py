import subprocess
import os
import pytest

SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "src")
BINARY = os.path.join(SRC_DIR, "sfinae_dispatch")
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
def test_arithmetic_const_ref():
    output = run_binary("test_arithmetic_const_ref")
    assert "PASS: test_arithmetic_const_ref" in output


@pytest.mark.fail_to_pass
def test_custom_const_ref():
    output = run_binary("test_custom_const_ref")
    assert "PASS: test_custom_const_ref" in output


@pytest.mark.fail_to_pass
def test_double_const_ref():
    output = run_binary("test_double_const_ref")
    assert "PASS: test_double_const_ref" in output


@pytest.mark.fail_to_pass
def test_fallback_const_ref():
    output = run_binary("test_fallback_const_ref")
    assert "PASS: test_fallback_const_ref" in output


# ── pass_to_pass ────────────────────────────────────────────────────────────

def test_arithmetic_value():
    output = run_binary("test_arithmetic_value")
    assert "PASS: test_arithmetic_value" in output


def test_custom_value():
    output = run_binary("test_custom_value")
    assert "PASS: test_custom_value" in output


def test_fallback():
    output = run_binary("test_fallback")
    assert "PASS: test_fallback" in output
