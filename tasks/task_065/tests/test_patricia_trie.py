import subprocess, os, pytest
SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "src")
BINARY = os.path.join(SRC_DIR, "patricia_trie")
if os.name == "nt": BINARY += ".exe"

def compile_cpp():
    r = subprocess.run(["g++", "-std=c++17", "-o", BINARY, os.path.join(SRC_DIR, "main.cpp")], capture_output=True, text=True)
    assert r.returncode == 0, f"Compilation failed:\n{r.stderr}"

def run_binary(t):
    compile_cpp()
    return subprocess.run([BINARY, t], capture_output=True, text=True, timeout=10).stdout.strip()

@pytest.mark.fail_to_pass
def test_prefix_then_full():
    assert "PASS: test_prefix_then_full" in run_binary("test_prefix_then_full")

@pytest.mark.fail_to_pass
def test_split_diverge():
    assert "PASS: test_split_diverge" in run_binary("test_split_diverge")

@pytest.mark.fail_to_pass
def test_all_keys():
    assert "PASS: test_all_keys" in run_binary("test_all_keys")

def test_insert_search_basic():
    assert "PASS: test_insert_search_basic" in run_binary("test_insert_search_basic")

def test_starts_with():
    assert "PASS: test_starts_with" in run_binary("test_starts_with")

def test_size():
    assert "PASS: test_size" in run_binary("test_size")
