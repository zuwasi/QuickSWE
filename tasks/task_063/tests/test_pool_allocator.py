import subprocess, os, pytest

SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "src")
BINARY = os.path.join(SRC_DIR, "pool_allocator")
if os.name == "nt": BINARY += ".exe"

def compile_cpp():
    r = subprocess.run(["g++", "-std=c++17", "-o", BINARY, os.path.join(SRC_DIR, "main.cpp")], capture_output=True, text=True)
    assert r.returncode == 0, f"Compilation failed:\n{r.stderr}"

def run_binary(test_name):
    compile_cpp()
    r = subprocess.run([BINARY, test_name], capture_output=True, text=True, timeout=10)
    return r.stdout.strip()

@pytest.mark.fail_to_pass
def test_basic_alloc_dealloc():
    assert "PASS: test_basic_alloc_dealloc" in run_binary("test_basic_alloc_dealloc")

@pytest.mark.fail_to_pass
def test_coalesce_adjacent():
    assert "PASS: test_coalesce_adjacent" in run_binary("test_coalesce_adjacent")

@pytest.mark.fail_to_pass
def test_coalesce_all_free():
    assert "PASS: test_coalesce_all_free" in run_binary("test_coalesce_all_free")

def test_simple_alloc():
    assert "PASS: test_simple_alloc" in run_binary("test_simple_alloc")

def test_available():
    assert "PASS: test_available" in run_binary("test_available")
