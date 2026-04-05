import subprocess, os, pytest
SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "src")
BINARY = os.path.join(SRC_DIR, "hamtrie")
if os.name == "nt": BINARY += ".exe"

def compile_cpp():
    r = subprocess.run(["g++", "-std=c++17", "-o", BINARY, os.path.join(SRC_DIR, "main.cpp")], capture_output=True, text=True)
    assert r.returncode == 0, f"Compilation failed:\n{r.stderr}"

def run_binary(t):
    compile_cpp()
    return subprocess.run([BINARY, t], capture_output=True, text=True, timeout=10).stdout.strip()

@pytest.mark.fail_to_pass
def test_persistence_insert():
    assert "PASS: test_persistence_insert" in run_binary("test_persistence_insert")

@pytest.mark.fail_to_pass
def test_persistence_remove():
    assert "PASS: test_persistence_remove" in run_binary("test_persistence_remove")

@pytest.mark.fail_to_pass
def test_overwrite():
    assert "PASS: test_overwrite" in run_binary("test_overwrite")

@pytest.mark.fail_to_pass
def test_many_keys():
    assert "PASS: test_many_keys" in run_binary("test_many_keys")

def test_insert_find():
    assert "PASS: test_insert_find" in run_binary("test_insert_find")

def test_empty():
    assert "PASS: test_empty" in run_binary("test_empty")

def test_all_entries():
    assert "PASS: test_all_entries" in run_binary("test_all_entries")
