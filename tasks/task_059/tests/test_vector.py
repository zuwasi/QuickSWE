import subprocess
import os
import pytest

SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "src")
BINARY = os.path.join(SRC_DIR, "vector")
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
def test_erase_single():
    output = run_binary("test_erase_single")
    assert "PASS: test_erase_single" in output


@pytest.mark.fail_to_pass
def test_erase_loop():
    output = run_binary("test_erase_loop")
    assert "PASS: test_erase_loop" in output


@pytest.mark.fail_to_pass
def test_erase_range():
    output = run_binary("test_erase_range")
    assert "PASS: test_erase_range" in output


@pytest.mark.fail_to_pass
def test_erase_range_all():
    output = run_binary("test_erase_range_all")
    assert "PASS: test_erase_range_all" in output


@pytest.mark.fail_to_pass
def test_erase_first():
    output = run_binary("test_erase_first")
    assert "PASS: test_erase_first" in output


# ── pass_to_pass ────────────────────────────────────────────────────────────

def test_push_after_erase():
    output = run_binary("test_push_after_erase")
    assert "PASS: test_push_after_erase" in output
