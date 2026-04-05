import subprocess, os, pytest
SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "src")
BINARY = os.path.join(SRC_DIR, "concurrent_map")
if os.name == "nt": BINARY += ".exe"

def compile_cpp():
    r = subprocess.run(["g++", "-std=c++17", "-O2", "-o", BINARY, os.path.join(SRC_DIR, "main.cpp"), "-lpthread"], capture_output=True, text=True)
    assert r.returncode == 0, f"Compilation failed:\n{r.stderr}"

def run_binary(t):
    compile_cpp()
    return subprocess.run([BINARY, t], capture_output=True, text=True, timeout=10).stdout.strip()

@pytest.mark.fail_to_pass
def test_insert_overwrite():
    assert "PASS: test_insert_overwrite" in run_binary("test_insert_overwrite")

@pytest.mark.fail_to_pass
def test_remove_then_find():
    assert "PASS: test_remove_then_find" in run_binary("test_remove_then_find")

@pytest.mark.fail_to_pass
def test_collision_chain():
    assert "PASS: test_collision_chain" in run_binary("test_collision_chain")

@pytest.mark.fail_to_pass
def test_remove_middle_of_chain():
    assert "PASS: test_remove_middle_of_chain" in run_binary("test_remove_middle_of_chain")

def test_insert_find():
    assert "PASS: test_insert_find" in run_binary("test_insert_find")

def test_contains():
    assert "PASS: test_contains" in run_binary("test_contains")

def test_all_entries():
    assert "PASS: test_all_entries" in run_binary("test_all_entries")
