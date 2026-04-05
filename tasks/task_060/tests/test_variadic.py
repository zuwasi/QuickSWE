import subprocess
import os
import pytest

SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "src")
BINARY = os.path.join(SRC_DIR, "variadic")
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
def test_all_of_false():
    output = run_binary("test_all_of_false")
    assert "PASS: test_all_of_false" in output


@pytest.mark.fail_to_pass
def test_any_of_true():
    output = run_binary("test_any_of_true")
    assert "PASS: test_any_of_true" in output


@pytest.mark.fail_to_pass
def test_any_of_false():
    output = run_binary("test_any_of_false")
    assert "PASS: test_any_of_false" in output


# ── pass_to_pass ────────────────────────────────────────────────────────────

def test_sum_all():
    output = run_binary("test_sum_all")
    assert "PASS: test_sum_all" in output


def test_transform_reduce():
    output = run_binary("test_transform_reduce")
    assert "PASS: test_transform_reduce" in output


def test_apply_to_each():
    output = run_binary("test_apply_to_each")
    assert "PASS: test_apply_to_each" in output


def test_min_of():
    output = run_binary("test_min_of")
    assert "PASS: test_min_of" in output
