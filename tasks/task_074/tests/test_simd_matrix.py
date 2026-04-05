import subprocess, os, pytest
SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "src")
BINARY = os.path.join(SRC_DIR, "simd_matrix")
if os.name == "nt": BINARY += ".exe"

def compile_cpp():
    r = subprocess.run(["g++", "-std=c++17", "-o", BINARY, os.path.join(SRC_DIR, "main.cpp")], capture_output=True, text=True)
    assert r.returncode == 0, f"Compilation failed:\n{r.stderr}"

def run_binary(t):
    compile_cpp()
    return subprocess.run([BINARY, t], capture_output=True, text=True, timeout=10).stdout.strip()

@pytest.mark.fail_to_pass
def test_identity_multiply():
    assert "PASS: test_identity_multiply" in run_binary("test_identity_multiply")

@pytest.mark.fail_to_pass
def test_multiply_general():
    assert "PASS: test_multiply_general" in run_binary("test_multiply_general")

@pytest.mark.fail_to_pass
def test_determinant_known():
    assert "PASS: test_determinant_known" in run_binary("test_determinant_known")

@pytest.mark.fail_to_pass
def test_multiply_known():
    assert "PASS: test_multiply_known" in run_binary("test_multiply_known")

def test_determinant_identity():
    assert "PASS: test_determinant_identity" in run_binary("test_determinant_identity")

def test_transpose():
    assert "PASS: test_transpose" in run_binary("test_transpose")

def test_add():
    assert "PASS: test_add" in run_binary("test_add")
