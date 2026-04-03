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


SOURCES = ['main.cpp']


# ---------------------------------------------------------------------------
# fail_to_pass: iterator features not yet implemented
# ---------------------------------------------------------------------------

@pytest.mark.fail_to_pass
def test_range_for():
    """SkipList should support range-for loops yielding sorted elements."""
    stdout, _, rc = compile_and_run(SOURCES, args=['range_for'])
    assert rc == 0
    assert stdout.strip() == "10 20 30 40 50"


@pytest.mark.fail_to_pass
def test_std_find():
    """std::find should work with SkipList iterators."""
    stdout, _, rc = compile_and_run(SOURCES, args=['std_find'])
    assert rc == 0
    assert "found=200" in stdout
    assert "not_found=true" in stdout


@pytest.mark.fail_to_pass
def test_std_count_if():
    """std::count_if should work with SkipList iterators."""
    stdout, _, rc = compile_and_run(SOURCES, args=['std_count_if'])
    assert rc == 0
    assert "count_gt_10=2" in stdout


@pytest.mark.fail_to_pass
def test_remove_and_iterate():
    """Iteration after removal should skip removed elements."""
    stdout, _, rc = compile_and_run(SOURCES, args=['remove_and_iterate'])
    assert rc == 0
    assert stdout.strip() == "1 3 4"


# ---------------------------------------------------------------------------
# pass_to_pass: basic skip list operations
# ---------------------------------------------------------------------------

def test_basic_ops():
    stdout, _, rc = compile_and_run(SOURCES, args=['basic_ops'])
    assert rc == 0
    assert "size=3" in stdout
    assert "contains_10=1" in stdout
    assert "contains_40=0" in stdout
