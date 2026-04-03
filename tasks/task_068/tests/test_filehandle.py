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


SOURCES = ['filehandle.cpp', 'main.cpp']


# ---------------------------------------------------------------------------
# fail_to_pass: double-free / unbalanced open/close
# ---------------------------------------------------------------------------

@pytest.mark.fail_to_pass
def test_vector_storage_balanced():
    """Storing FileHandles in a vector should not cause double-close."""
    stdout, _, rc = compile_and_run(SOURCES, args=['vector_storage'])
    assert rc == 0
    assert "size=2" in stdout
    assert "balanced=1" in stdout


@pytest.mark.fail_to_pass
def test_move_semantics():
    """Move constructor should transfer ownership, not duplicate it."""
    stdout, _, rc = compile_and_run(SOURCES, args=['move_semantics'])
    assert rc == 0
    assert "fh2_valid=1" in stdout
    assert "balanced=1" in stdout


# ---------------------------------------------------------------------------
# pass_to_pass: basic open/close without copying
# ---------------------------------------------------------------------------

def test_basic_open_close():
    stdout, _, rc = compile_and_run(SOURCES, args=['basic_open_close'])
    assert rc == 0
    assert "valid=1" in stdout
    assert "balanced=1" in stdout


def test_factory_return():
    """Factory return works due to NRVO/copy elision — passes even with bug."""
    stdout, _, rc = compile_and_run(SOURCES, args=['factory_return'])
    assert rc == 0
    assert "path=data.bin" in stdout
