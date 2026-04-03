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


SOURCES = ['matrix.c', 'main.c']


# ---------------------------------------------------------------------------
# fail_to_pass: the wrong-index bug produces incorrect results for non-square
# ---------------------------------------------------------------------------

@pytest.mark.fail_to_pass
def test_rect_2x3_times_3x2():
    """Non-square multiplication: bug writes to C[i][k] instead of C[i][j]."""
    stdout, _, rc = compile_and_run(SOURCES, args=['rect_2x3_times_3x2'])
    assert rc == 0
    lines = stdout.strip().split('\n')
    assert len(lines) == 2
    row0 = lines[0].split()
    row1 = lines[1].split()
    assert int(row0[0]) == 58,  f"C[0][0] expected 58, got {row0[0]}"
    assert int(row0[1]) == 64,  f"C[0][1] expected 64, got {row0[1]}"
    assert int(row1[0]) == 139, f"C[1][0] expected 139, got {row1[0]}"
    assert int(row1[1]) == 154, f"C[1][1] expected 154, got {row1[1]}"


@pytest.mark.fail_to_pass
def test_rect_1x3_times_3x1():
    """Dot product via 1x3 * 3x1 = 1x1 scalar."""
    stdout, _, rc = compile_and_run(SOURCES, args=['rect_1x3_times_3x1'])
    assert rc == 0
    assert stdout.strip() == "20"


# ---------------------------------------------------------------------------
# pass_to_pass: square identity multiplication happens to work
# ---------------------------------------------------------------------------

def test_square_diagonal():
    """Diagonal × diagonal accidentally works even with the bug."""
    stdout, _, rc = compile_and_run(SOURCES, args=['square_diagonal'])
    assert rc == 0
    lines = stdout.strip().split('\n')
    assert len(lines) == 2
    assert lines[0].split() == ['6', '0']
    assert lines[1].split() == ['0', '20']


def test_dimension_mismatch():
    stdout, _, rc = compile_and_run(SOURCES, args=['dimension_mismatch'])
    assert rc == 0
    assert "rc=-1" in stdout
