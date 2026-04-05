import subprocess
import os
import pytest

SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "src")
BINARY = os.path.join(SRC_DIR, "shared_ptr")
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
def test_self_assignment():
    output = run_binary("test_self_assignment")
    assert "PASS: test_self_assignment" in output


@pytest.mark.fail_to_pass
def test_copy_assign_releases_old():
    output = run_binary("test_copy_assign_releases_old")
    assert "PASS: test_copy_assign_releases_old" in output


@pytest.mark.fail_to_pass
def test_chain_assignment():
    output = run_binary("test_chain_assignment")
    lines = output.split("\n")
    assert any("PASS: test_chain_assignment" in l for l in lines)
    assert any("PASS: test_chain_no_leak" in l for l in lines)


# ── pass_to_pass ────────────────────────────────────────────────────────────

def test_basic_usage():
    output = run_binary("test_basic_usage")
    assert "PASS: test_basic_usage" in output


def test_copy_construct():
    output = run_binary("test_copy_construct")
    assert "PASS: test_copy_construct" in output


def test_move():
    output = run_binary("test_move")
    assert "PASS: test_move" in output
