import subprocess
import os
import sys
import tempfile
import platform
import pytest


def compile_c(src_files, output_name, extra_flags=None):
    """Compile C files with gcc, return path to executable."""
    src_dir = os.path.join(os.path.dirname(__file__), '..', 'src')
    sources = [os.path.join(src_dir, f) for f in src_files]
    tmp = tempfile.mkdtemp()
    ext = '.exe' if platform.system() == 'Windows' else ''
    out_path = os.path.join(tmp, output_name + ext)
    cmd = ['gcc'] + sources + ['-o', out_path, '-lm']
    if extra_flags:
        cmd.extend(extra_flags)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed:\n{result.stderr}")
    return out_path


def run_binary(path, stdin_data=None, args=None):
    """Run compiled binary and return (stdout, stderr, returncode)."""
    cmd = [path] + (args or [])
    result = subprocess.run(cmd, capture_output=True, text=True,
                            input=stdin_data, timeout=10)
    return result.stdout, result.stderr, result.returncode


@pytest.fixture(scope="module")
def dynarray_binary():
    """Compile the dynarray program once for the module."""
    return compile_c(['dynarray.c', 'main.c'], 'dynarray_test')


# ---- pass_to_pass: these should pass even with the buggy code ----

class TestPassToPass:
    """Tests that verify basic functionality that works even in buggy code."""

    def test_compilation_succeeds(self):
        """The code should at least compile without errors."""
        binary = compile_c(['dynarray.c', 'main.c'], 'dynarray_compile_check')
        assert os.path.exists(binary)

    def test_program_runs(self, dynarray_binary):
        """The program should run and print usage when called without args."""
        stdout, stderr, rc = run_binary(dynarray_binary)
        assert "Usage" in stdout or rc != 0


# ---- fail_to_pass: these FAIL on the buggy code, PASS after fix ----

class TestFailToPass:

    @pytest.mark.fail_to_pass
    def test_basic_push_and_get(self, dynarray_binary):
        """Push 10 values and read them back. Fails because capacity=0 realloc bug."""
        stdout, stderr, rc = run_binary(dynarray_binary, args=['basic_push_get'])
        assert rc == 0, f"Program crashed or returned error. stderr: {stderr}"
        assert "PASS: basic_push_get" in stdout, f"Got: {stdout}"

    @pytest.mark.fail_to_pass
    def test_bounds_check(self, dynarray_binary):
        """Out-of-bounds get should return error. Fails because no bounds checking."""
        stdout, stderr, rc = run_binary(dynarray_binary, args=['bounds_check'])
        assert "PASS: bounds_check" in stdout, f"Bounds check not enforced. Got: {stdout}"

    @pytest.mark.fail_to_pass
    def test_grow_large(self, dynarray_binary):
        """Push 1000 elements and verify all. Fails due to capacity=0 realloc bug."""
        stdout, stderr, rc = run_binary(dynarray_binary, args=['grow_large'])
        assert rc == 0, f"Program crashed. stderr: {stderr}"
        assert "PASS: grow_large" in stdout, f"Got: {stdout}"
