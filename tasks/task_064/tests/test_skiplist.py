import subprocess, os, pytest
SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "src")
BINARY = os.path.join(SRC_DIR, "skiplist")
if os.name == "nt": BINARY += ".exe"

def compile_cpp():
    r = subprocess.run(["g++", "-std=c++17", "-o", BINARY, os.path.join(SRC_DIR, "main.cpp")], capture_output=True, text=True)
    assert r.returncode == 0, f"Compilation failed:\n{r.stderr}"

def run_binary(t):
    compile_cpp()
    return subprocess.run([BINARY, t], capture_output=True, text=True, timeout=10).stdout.strip()

@pytest.mark.fail_to_pass
def test_insert_search():
    assert "PASS: test_insert_search" in run_binary("test_insert_search")

@pytest.mark.fail_to_pass
def test_forward_pointers():
    assert "PASS: test_forward_pointers" in run_binary("test_forward_pointers")

@pytest.mark.fail_to_pass
def test_remove_updates_level():
    assert "PASS: test_remove_updates_level" in run_binary("test_remove_updates_level")

def test_to_vector_sorted():
    assert "PASS: test_to_vector_sorted" in run_binary("test_to_vector_sorted")

def test_size():
    assert "PASS: test_size" in run_binary("test_size")
