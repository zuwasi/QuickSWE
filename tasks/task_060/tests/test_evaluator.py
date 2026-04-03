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


SOURCES = ['stack.c', 'evaluator.c']


# ---------------------------------------------------------------------------
# fail_to_pass: these tests expose the bugs
# ---------------------------------------------------------------------------

@pytest.mark.fail_to_pass
def test_stack_overflow():
    """Pushing more than MAX_STACK_SIZE items should produce an overflow error, not crash."""
    # Expression "1 2 3 4 5" pushes 5 numbers onto a stack of size 4
    stdout, stderr, rc = compile_and_run(SOURCES, args=['1 2 3 4 5'])
    # Should not crash — should report overflow
    assert rc != 0 or "ERROR" in stdout
    assert "overflow" in stdout.lower()


@pytest.mark.fail_to_pass
def test_division_by_zero():
    """Division by zero should produce an error message, not crash."""
    stdout, stderr, rc = compile_and_run(SOURCES, args=['10 0 /'])
    assert "ERROR" in stdout
    assert "division by zero" in stdout.lower() or "divide by zero" in stdout.lower()


# ---------------------------------------------------------------------------
# pass_to_pass: these tests already pass with the buggy code
# ---------------------------------------------------------------------------

def test_simple_addition():
    stdout, _, rc = compile_and_run(SOURCES, args=['3 4 +'])
    assert rc == 0
    assert stdout == "7"


def test_simple_subtraction():
    stdout, _, rc = compile_and_run(SOURCES, args=['10 3 -'])
    assert rc == 0
    assert stdout == "7"


def test_multiplication():
    stdout, _, rc = compile_and_run(SOURCES, args=['6 7 *'])
    assert rc == 0
    assert stdout == "42"


def test_compound_expression():
    """3 4 + 2 * = (3+4)*2 = 14"""
    stdout, _, rc = compile_and_run(SOURCES, args=['3 4 + 2 *'])
    assert rc == 0
    assert stdout == "14"


def test_stack_underflow_error():
    """Operator with insufficient operands should report underflow."""
    stdout, _, rc = compile_and_run(SOURCES, args=['+'])
    assert "ERROR" in stdout
    assert "underflow" in stdout.lower()
