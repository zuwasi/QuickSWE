import subprocess, os, pytest
SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "src")
BINARY = os.path.join(SRC_DIR, "scheduler")
if os.name == "nt": BINARY += ".exe"

def compile_cpp():
    r = subprocess.run(["g++", "-std=c++17", "-o", BINARY, os.path.join(SRC_DIR, "main.cpp")], capture_output=True, text=True)
    assert r.returncode == 0, f"Compilation failed:\n{r.stderr}"

def run_binary(t):
    compile_cpp()
    return subprocess.run([BINARY, t], capture_output=True, text=True, timeout=10).stdout.strip()

@pytest.mark.fail_to_pass
def test_round_robin_order():
    assert "PASS: test_round_robin_order" in run_binary("test_round_robin_order")

@pytest.mark.fail_to_pass
def test_yield_preserves_state():
    assert "PASS: test_yield_preserves_state" in run_binary("test_yield_preserves_state")

@pytest.mark.fail_to_pass
def test_multiple_tasks_complete():
    assert "PASS: test_multiple_tasks_complete" in run_binary("test_multiple_tasks_complete")

def test_single_task():
    assert "PASS: test_single_task" in run_binary("test_single_task")

def test_join_completed():
    assert "PASS: test_join_completed" in run_binary("test_join_completed")
