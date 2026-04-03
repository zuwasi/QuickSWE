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
def queue_binary():
    return compile_c(['queue.c', 'main.c'], 'queue_test')


# ---- pass_to_pass ----

class TestPassToPass:

    def test_compilation(self):
        binary = compile_c(['queue.c', 'main.c'], 'queue_compile')
        assert os.path.exists(binary)

    def test_basic_push_pop(self, queue_binary):
        """Simple push/pop without interleaving should work."""
        stdout, stderr, rc = run_binary(queue_binary, args=['basic_push_pop'])
        assert rc == 0
        assert "PASS: basic_push_pop" in stdout


# ---- fail_to_pass ----

class TestFailToPass:

    @pytest.mark.fail_to_pass
    def test_interleave_race_condition(self, queue_binary):
        """
        Simulated interleaving exposes the if-vs-while bug:
        Consumer A waits, producer pushes, consumer B takes it,
        consumer A resumes and pops from empty queue.
        """
        stdout, stderr, rc = run_binary(queue_binary, args=['interleave_race'])
        assert rc == 0, f"Crashed: {stderr}"
        assert "RESULT: NO_RACE" in stdout, (
            f"Race condition detected — resume_pop didn't re-check emptiness.\n{stdout}"
        )

    @pytest.mark.fail_to_pass
    def test_count_integrity(self, queue_binary):
        """Queue count should never go negative."""
        stdout, stderr, rc = run_binary(queue_binary, args=['count_integrity'])
        assert rc == 0, f"Crashed: {stderr}"
        assert "RESULT: COUNT_OK" in stdout, (
            f"Count underflowed below zero due to buggy resume_pop.\n{stdout}"
        )

    @pytest.mark.fail_to_pass
    def test_no_items_lost(self, queue_binary):
        """All pushed items should be popped with consistent sums."""
        stdout, stderr, rc = run_binary(queue_binary, args=['multi_interleave'])
        assert rc == 0, f"Crashed: {stderr}"
        assert "RESULT: CONSISTENT" in stdout, (
            f"Items were lost due to race condition.\n{stdout}"
        )
