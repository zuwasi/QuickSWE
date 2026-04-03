import subprocess
import os
import sys
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


# ---------------------------------------------------------------------------
# fail_to_pass: these tests expose the bugs
# ---------------------------------------------------------------------------

@pytest.mark.fail_to_pass
def test_negative_keys():
    """Hash function returns negative index for negative keys, causing crash or wrong bucket."""
    stdout, stderr, rc = compile_and_run(
        ['hashtable.c', 'main.c'], compiler='gcc', args=['negative_keys']
    )
    assert rc == 0, f"Program crashed (rc={rc}): {stderr}"
    assert "-5=500" in stdout
    assert "-10=1000" in stdout
    assert "-1=100" in stdout


@pytest.mark.fail_to_pass
def test_resize_rehash():
    """After resize, entries must be rehashed to correct buckets."""
    stdout, stderr, rc = compile_and_run(
        ['hashtable.c', 'main.c'], compiler='gcc', args=['resize_rehash']
    )
    assert rc == 0, f"Program crashed (rc={rc}): {stderr}"
    assert "ALL_FOUND" in stdout
    assert "MISSING" not in stdout


# ---------------------------------------------------------------------------
# pass_to_pass: these tests already pass with the buggy code
# ---------------------------------------------------------------------------

def test_basic_insert_get():
    stdout, stderr, rc = compile_and_run(
        ['hashtable.c', 'main.c'], compiler='gcc', args=['basic_insert_get']
    )
    assert rc == 0
    assert "1=10" in stdout
    assert "2=20" in stdout
    assert "3=30" in stdout


def test_update_value():
    stdout, stderr, rc = compile_and_run(
        ['hashtable.c', 'main.c'], compiler='gcc', args=['update_value']
    )
    assert rc == 0
    assert "42=2" in stdout


def test_remove():
    stdout, stderr, rc = compile_and_run(
        ['hashtable.c', 'main.c'], compiler='gcc', args=['remove']
    )
    assert rc == 0
    assert "10=NOT_FOUND" in stdout
    assert "20=200" in stdout
