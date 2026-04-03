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


SOURCES = ['resource_manager.cpp', 'main.cpp']


# ---------------------------------------------------------------------------
# fail_to_pass: use-after-move crashes
# ---------------------------------------------------------------------------

@pytest.mark.fail_to_pass
def test_transfer_and_access():
    """Transferring a resource should not crash; moved-from ptr should be null."""
    stdout, stderr, rc = compile_and_run(SOURCES, args=['transfer_and_access'])
    assert rc == 0, f"Program crashed (rc={rc}): {stderr}"
    assert "after_transfer_0=NULL_RESOURCE" in stdout
    assert "still_valid_1=" in stdout
    assert "count=2" in stdout


@pytest.mark.fail_to_pass
def test_transfer_all():
    """Transferring all resources should not crash."""
    stdout, stderr, rc = compile_and_run(SOURCES, args=['transfer_all'])
    assert rc == 0, f"Program crashed (rc={rc}): {stderr}"
    assert "count=0" in stdout


# ---------------------------------------------------------------------------
# pass_to_pass: basic operations that work without triggering the bug
# ---------------------------------------------------------------------------

def test_add_and_info():
    stdout, _, rc = compile_and_run(SOURCES, args=['add_and_info'])
    assert rc == 0
    assert "Resource(1,TextureA,5)" in stdout
    assert "Resource(2,MeshB,3)" in stdout
    assert "count=2" in stdout


def test_invalid_index():
    stdout, _, rc = compile_and_run(SOURCES, args=['invalid_index'])
    assert rc == 0
    assert "INVALID_INDEX" in stdout


def test_get_all():
    stdout, _, rc = compile_and_run(SOURCES, args=['get_all'])
    assert rc == 0
    assert "Resource(1,A,1)" in stdout
    assert "Resource(2,B,2)" in stdout
