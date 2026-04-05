import subprocess
import os
import pytest

SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "src")
BINARY = os.path.join(SRC_DIR, "hashmap")
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
def test_lookup_after_delete():
    output = run_binary("test_lookup_after_delete")
    assert "PASS: test_lookup_after_delete" in output


@pytest.mark.fail_to_pass
def test_lookup_chain_after_delete():
    output = run_binary("test_lookup_chain_after_delete")
    assert "PASS: test_lookup_chain_after_delete" in output


@pytest.mark.fail_to_pass
def test_reinsert_after_delete():
    output = run_binary("test_reinsert_after_delete")
    assert "PASS: test_reinsert_after_delete" in output


# ── pass_to_pass ────────────────────────────────────────────────────────────

def test_basic_insert_get():
    output = run_binary("test_basic_insert_get")
    assert "PASS: test_basic_insert_get" in output


def test_contains():
    output = run_binary("test_contains")
    assert "PASS: test_contains" in output


def test_overwrite():
    output = run_binary("test_overwrite")
    assert "PASS: test_overwrite" in output
