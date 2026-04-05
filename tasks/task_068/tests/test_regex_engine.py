import subprocess, os, pytest
SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "src")
BINARY = os.path.join(SRC_DIR, "regex_engine")
if os.name == "nt": BINARY += ".exe"

def compile_cpp():
    r = subprocess.run(["g++", "-std=c++17", "-o", BINARY, os.path.join(SRC_DIR, "main.cpp")], capture_output=True, text=True)
    assert r.returncode == 0, f"Compilation failed:\n{r.stderr}"

def run_binary(t):
    compile_cpp()
    return subprocess.run([BINARY, t], capture_output=True, text=True, timeout=10).stdout.strip()

@pytest.mark.fail_to_pass
def test_alternation():
    assert "PASS: test_alternation" in run_binary("test_alternation")

@pytest.mark.fail_to_pass
def test_star():
    assert "PASS: test_star" in run_binary("test_star")

@pytest.mark.fail_to_pass
def test_plus():
    assert "PASS: test_plus" in run_binary("test_plus")

@pytest.mark.fail_to_pass
def test_complex_pattern():
    assert "PASS: test_complex_pattern" in run_binary("test_complex_pattern")

def test_literal():
    assert "PASS: test_literal" in run_binary("test_literal")

def test_question():
    assert "PASS: test_question" in run_binary("test_question")
