import subprocess
import os
import tempfile
import platform
import pytest


def compile_and_run(src_files, compiler="gcc", flags=None, stdin_data=None, args=None):
    src_dir = os.path.join(os.path.dirname(__file__), '..', 'src')
    sources = [os.path.join(src_dir, f) for f in src_files]
    tmp = tempfile.mkdtemp()
    ext = '.exe' if platform.system() == 'Windows' else ''
    out = os.path.join(tmp, 'prog' + ext)
    cmd = [compiler] + sources + ['-o', out] + (flags or [])
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == 0, f"Compile failed: {r.stderr}"
    r = subprocess.run([out] + (args or []), capture_output=True, text=True, input=stdin_data, timeout=10)
    return r.stdout.strip(), r.stderr, r.returncode


SOURCES = ['circbuf.c', 'main.c']


# ---------------------------------------------------------------------------
# fail_to_pass: wrap-around bugs
# ---------------------------------------------------------------------------

@pytest.mark.fail_to_pass
def test_wrap_around_read():
    """After write wraps, read should still return correct items."""
    stdout, _, rc = compile_and_run(SOURCES, args=['wrap_around'])
    assert rc == 0
    assert "r3=300" in stdout
    assert "r4=400" in stdout
    assert "r5=500" in stdout
    assert "r3=FAIL" not in stdout


@pytest.mark.fail_to_pass
def test_count_after_wrap():
    """cb_count should be correct after write_pos wraps past read_pos."""
    stdout, _, rc = compile_and_run(SOURCES, args=['count_after_wrap'])
    assert rc == 0
    assert "count=1" in stdout
    assert "val=40" in stdout
    assert "val=FAIL" not in stdout


@pytest.mark.fail_to_pass
def test_wrap_count_value():
    """Count should be 3 when buffer has 3 items after wrap."""
    stdout, _, rc = compile_and_run(SOURCES, args=['wrap_around'])
    assert rc == 0
    assert "count=3" in stdout


# ---------------------------------------------------------------------------
# pass_to_pass: basic operations without wrap
# ---------------------------------------------------------------------------

def test_basic_write_read():
    stdout, _, rc = compile_and_run(SOURCES, args=['basic_write_read'])
    assert rc == 0
    assert "10" in stdout
    assert "20" in stdout
    assert "empty=1" in stdout


def test_full_check():
    stdout, _, rc = compile_and_run(SOURCES, args=['full_check'])
    assert rc == 0
    assert "write_full_rc=-1" in stdout
    assert "full=1" in stdout
