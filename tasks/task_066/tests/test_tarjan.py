import subprocess, os, pytest
SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "src")
BINARY = os.path.join(SRC_DIR, "tarjan")
if os.name == "nt": BINARY += ".exe"

def compile_cpp():
    r = subprocess.run(["g++", "-std=c++17", "-o", BINARY, os.path.join(SRC_DIR, "main.cpp")], capture_output=True, text=True)
    assert r.returncode == 0, f"Compilation failed:\n{r.stderr}"

def run_binary(t):
    compile_cpp()
    return subprocess.run([BINARY, t], capture_output=True, text=True, timeout=10).stdout.strip()

@pytest.mark.fail_to_pass
def test_dag():
    assert "PASS: test_dag" in run_binary("test_dag")

@pytest.mark.fail_to_pass
def test_two_sccs():
    assert "PASS: test_two_sccs" in run_binary("test_two_sccs")

@pytest.mark.fail_to_pass
def test_cross_edge_no_merge():
    assert "PASS: test_cross_edge_no_merge" in run_binary("test_cross_edge_no_merge")

def test_simple_cycle():
    assert "PASS: test_simple_cycle" in run_binary("test_simple_cycle")

def test_single_node():
    assert "PASS: test_single_node" in run_binary("test_single_node")
