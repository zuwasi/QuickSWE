import subprocess, os, pytest
SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "src")
BINARY = os.path.join(SRC_DIR, "btree_lazy")
if os.name == "nt": BINARY += ".exe"

def compile_cpp():
    r = subprocess.run(["g++", "-std=c++17", "-o", BINARY, os.path.join(SRC_DIR, "main.cpp")], capture_output=True, text=True)
    assert r.returncode == 0, f"Compilation failed:\n{r.stderr}"

def run_binary(t):
    compile_cpp()
    return subprocess.run([BINARY, t], capture_output=True, text=True, timeout=10).stdout.strip()

@pytest.mark.fail_to_pass
def test_compact_preserves_keys():
    assert "PASS: test_compact_preserves_keys" in run_binary("test_compact_preserves_keys")

@pytest.mark.fail_to_pass
def test_inorder_after_compact():
    assert "PASS: test_inorder_after_compact" in run_binary("test_inorder_after_compact")

@pytest.mark.fail_to_pass
def test_heavy_delete_compact():
    assert "PASS: test_heavy_delete_compact" in run_binary("test_heavy_delete_compact")

def test_insert_search():
    assert "PASS: test_insert_search" in run_binary("test_insert_search")

def test_lazy_remove():
    assert "PASS: test_lazy_remove" in run_binary("test_lazy_remove")

def test_inorder_basic():
    assert "PASS: test_inorder_basic" in run_binary("test_inorder_basic")
