import subprocess
import os
import sys
import tempfile
import platform
import pytest


def compile_cpp(src_files, output_name, extra_flags=None):
    """Compile C++ files with g++, return path to executable."""
    src_dir = os.path.join(os.path.dirname(__file__), '..', 'src')
    sources = [os.path.join(src_dir, f) for f in src_files]
    tmp = tempfile.mkdtemp()
    ext = '.exe' if platform.system() == 'Windows' else ''
    out_path = os.path.join(tmp, output_name + ext)
    cmd = ['g++', '-std=c++17'] + sources + ['-o', out_path]
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
def bst_binary():
    return compile_cpp(['main.cpp'], 'bst_test')


# ---- pass_to_pass ----

class TestPassToPass:

    def test_compilation(self):
        binary = compile_cpp(['main.cpp'], 'bst_compile')
        assert os.path.exists(binary)

    def test_basic_insert_find(self, bst_binary):
        stdout, stderr, rc = run_binary(bst_binary, args=['basic_insert_find'])
        assert rc == 0
        assert "PASS: basic_insert_find" in stdout

    def test_delete_leaf(self, bst_binary):
        stdout, stderr, rc = run_binary(bst_binary, args=['delete_leaf'])
        assert rc == 0
        assert "PASS: delete_leaf" in stdout


# ---- fail_to_pass ----

class TestFailToPass:

    @pytest.mark.fail_to_pass
    def test_delete_node_with_two_children(self, bst_binary):
        """Deleting a node with two children should preserve all other nodes."""
        stdout, stderr, rc = run_binary(bst_binary, args=['delete_two_children'])
        assert rc == 0, f"Crashed: {stderr}"
        assert "RESULT: CORRECT" in stdout, (
            f"Tree corrupted after deleting node with two children.\n{stdout}"
        )

    @pytest.mark.fail_to_pass
    def test_delete_successor_is_right_child(self, bst_binary):
        """When successor is the immediate right child, its children must be kept."""
        stdout, stderr, rc = run_binary(bst_binary, args=['delete_successor_is_right_child'])
        assert rc == 0, f"Crashed: {stderr}"
        assert "RESULT: CORRECT" in stdout, (
            f"Tree corrupted when successor was immediate right child.\n{stdout}"
        )

    @pytest.mark.fail_to_pass
    def test_multiple_deletes(self, bst_binary):
        """Multiple deletions of two-children nodes should keep tree valid."""
        stdout, stderr, rc = run_binary(bst_binary, args=['multiple_deletes'])
        assert rc == 0, f"Crashed: {stderr}"
        assert "RESULT: CORRECT" in stdout, (
            f"Tree corrupted after multiple deletions.\n{stdout}"
        )
