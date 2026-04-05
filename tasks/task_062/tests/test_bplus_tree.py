import subprocess
import os
import pytest

SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "src")
BINARY = os.path.join(SRC_DIR, "bplus_tree")
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


@pytest.mark.fail_to_pass
def test_remove_keeps_others():
    output = run_binary("test_remove_keeps_others")
    assert "PASS: test_remove_keeps_others" in output

@pytest.mark.fail_to_pass
def test_redistribute_updates_parent():
    output = run_binary("test_redistribute_updates_parent")
    assert "PASS: test_redistribute_updates_parent" in output

@pytest.mark.fail_to_pass
def test_range_after_delete():
    output = run_binary("test_range_after_delete")
    assert "PASS: test_range_after_delete" in output

def test_insert_search():
    output = run_binary("test_insert_search")
    assert "PASS: test_insert_search" in output

def test_all_keys_sorted():
    output = run_binary("test_all_keys_sorted")
    assert "PASS: test_all_keys_sorted" in output

def test_range_query_basic():
    output = run_binary("test_range_query_basic")
    assert "PASS: test_range_query_basic" in output
