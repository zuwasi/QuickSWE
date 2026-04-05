import subprocess, os, pytest
SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "src")
BINARY = os.path.join(SRC_DIR, "gc")
if os.name == "nt": BINARY += ".exe"

def compile_cpp():
    r = subprocess.run(["g++", "-std=c++17", "-o", BINARY, os.path.join(SRC_DIR, "main.cpp")], capture_output=True, text=True)
    assert r.returncode == 0, f"Compilation failed:\n{r.stderr}"

def run_binary(t):
    compile_cpp()
    return subprocess.run([BINARY, t], capture_output=True, text=True, timeout=10).stdout.strip()

@pytest.mark.fail_to_pass
def test_transitive_reachability():
    assert "PASS: test_transitive_reachability" in run_binary("test_transitive_reachability")

@pytest.mark.fail_to_pass
def test_cycle_collection():
    assert "PASS: test_cycle_collection" in run_binary("test_cycle_collection")

@pytest.mark.fail_to_pass
def test_multiple_cycles():
    assert "PASS: test_multiple_cycles" in run_binary("test_multiple_cycles")

def test_basic_collect():
    assert "PASS: test_basic_collect" in run_binary("test_basic_collect")

def test_no_roots_collect_all():
    assert "PASS: test_no_roots_collect_all" in run_binary("test_no_roots_collect_all")

def test_refs_after_compact():
    assert "PASS: test_refs_after_compact" in run_binary("test_refs_after_compact")
