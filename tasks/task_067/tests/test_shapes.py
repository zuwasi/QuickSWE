import subprocess
import os
import tempfile
import platform
import pytest


def compile_and_run(src_files, compiler="g++", flags=None, stdin_data=None, args=None):
    src_dir = os.path.join(os.path.dirname(__file__), '..', 'src')
    sources = [os.path.join(src_dir, f) for f in src_files]
    tmp = tempfile.mkdtemp()
    ext = '.exe' if platform.system() == 'Windows' else ''
    out = os.path.join(tmp, 'prog' + ext)
    cmd = [compiler] + sources + ['-o', out] + (flags or ['-std=c++17'])
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == 0, f"Compile failed: {r.stderr}"
    r = subprocess.run([out] + (args or []), capture_output=True, text=True, input=stdin_data, timeout=10)
    return r.stdout.strip(), r.stderr, r.returncode


SOURCES = ['shapes.cpp', 'main.cpp']


# ---------------------------------------------------------------------------
# fail_to_pass: slicing bugs cause wrong name/area
# ---------------------------------------------------------------------------

@pytest.mark.fail_to_pass
def test_factory_circle():
    """Factory-created circle should have name='Circle' and area≈79."""
    stdout, _, rc = compile_and_run(SOURCES, args=['factory_circle'])
    assert rc == 0
    assert "name=Circle" in stdout
    assert "area=79" in stdout  # pi*25 ≈ 78.54, rounded to 79


@pytest.mark.fail_to_pass
def test_factory_rectangle():
    """Factory-created rectangle should have name='Rectangle' and area=24."""
    stdout, _, rc = compile_and_run(SOURCES, args=['factory_rectangle'])
    assert rc == 0
    assert "name=Rectangle" in stdout
    assert "area=24" in stdout


@pytest.mark.fail_to_pass
def test_process_shapes():
    """Shapes stored in a vector should preserve polymorphic behavior."""
    stdout, _, rc = compile_and_run(SOURCES, args=['process_shapes'])
    assert rc == 0
    assert "Circle" in stdout
    assert "Rectangle" in stdout
    # Verify areas are not 0
    assert "area=0.0" not in stdout


# ---------------------------------------------------------------------------
# pass_to_pass: direct construction without slicing
# ---------------------------------------------------------------------------

def test_direct_circle():
    stdout, _, rc = compile_and_run(SOURCES, args=['direct_circle'])
    assert rc == 0
    assert "name=Circle" in stdout
    assert "area=79" in stdout


def test_direct_rectangle():
    stdout, _, rc = compile_and_run(SOURCES, args=['direct_rectangle'])
    assert rc == 0
    assert "name=Rectangle" in stdout
    assert "area=24" in stdout
