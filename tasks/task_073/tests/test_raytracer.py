import subprocess, os, pytest
SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "src")
BINARY = os.path.join(SRC_DIR, "raytracer")
if os.name == "nt": BINARY += ".exe"

def compile_cpp():
    r = subprocess.run(["g++", "-std=c++17", "-o", BINARY, os.path.join(SRC_DIR, "main.cpp")], capture_output=True, text=True)
    assert r.returncode == 0, f"Compilation failed:\n{r.stderr}"

def run_binary(t):
    compile_cpp()
    return subprocess.run([BINARY, t], capture_output=True, text=True, timeout=10).stdout.strip()

@pytest.mark.fail_to_pass
def test_reflect_basic():
    assert "PASS: test_reflect_basic" in run_binary("test_reflect_basic")

@pytest.mark.fail_to_pass
def test_reflect_45deg():
    assert "PASS: test_reflect_45deg" in run_binary("test_reflect_45deg")

@pytest.mark.fail_to_pass
def test_sphere_intersect():
    assert "PASS: test_sphere_intersect" in run_binary("test_sphere_intersect")

@pytest.mark.fail_to_pass
def test_nearest_hit():
    assert "PASS: test_nearest_hit" in run_binary("test_nearest_hit")

@pytest.mark.fail_to_pass
def test_trace_hit():
    assert "PASS: test_trace_hit" in run_binary("test_trace_hit")

def test_sphere_miss():
    assert "PASS: test_sphere_miss" in run_binary("test_sphere_miss")

def test_vec3_normalize():
    assert "PASS: test_vec3_normalize" in run_binary("test_vec3_normalize")
