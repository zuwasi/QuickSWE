import subprocess, os, pytest
SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "src")
BINARY = os.path.join(SRC_DIR, "pratt_parser")
if os.name == "nt": BINARY += ".exe"

def compile_cpp():
    r = subprocess.run(["g++", "-std=c++17", "-o", BINARY, os.path.join(SRC_DIR, "main.cpp")], capture_output=True, text=True)
    assert r.returncode == 0, f"Compilation failed:\n{r.stderr}"

def run_binary(t):
    compile_cpp()
    return subprocess.run([BINARY, t], capture_output=True, text=True, timeout=10).stdout.strip()

@pytest.mark.fail_to_pass
def test_precedence():
    assert "PASS: test_precedence" in run_binary("test_precedence")

@pytest.mark.fail_to_pass
def test_power_right_assoc():
    assert "PASS: test_power_right_assoc" in run_binary("test_power_right_assoc")

@pytest.mark.fail_to_pass
def test_complex():
    assert "PASS: test_complex" in run_binary("test_complex")

def test_simple_add():
    assert "PASS: test_simple_add" in run_binary("test_simple_add")

def test_unary_minus():
    assert "PASS: test_unary_minus" in run_binary("test_unary_minus")

def test_parens():
    assert "PASS: test_parens" in run_binary("test_parens")

def test_nested_parens():
    assert "PASS: test_nested_parens" in run_binary("test_nested_parens")
