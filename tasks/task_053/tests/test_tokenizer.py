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
def tokenizer_binary():
    return compile_c(['tokenizer.c', 'main.c'], 'tokenizer_test')


# ---- pass_to_pass ----

class TestPassToPass:

    def test_compilation(self):
        binary = compile_c(['tokenizer.c', 'main.c'], 'tokenizer_compile')
        assert os.path.exists(binary)

    def test_simple_split(self, tokenizer_binary):
        """Simple comma splitting should work in current code."""
        stdout, stderr, rc = run_binary(tokenizer_binary, args=['simple_split'])
        assert rc == 0
        assert "COUNT: 3" in stdout
        assert "TOKEN[0]: [hello]" in stdout
        assert "TOKEN[1]: [world]" in stdout
        assert "TOKEN[2]: [foo]" in stdout

    def test_empty_tokens(self, tokenizer_binary):
        """Empty tokens between delimiters should be preserved."""
        stdout, stderr, rc = run_binary(tokenizer_binary, args=['empty_tokens'])
        assert rc == 0
        assert "COUNT: 3" in stdout
        assert "TOKEN[0]: [a]" in stdout
        assert "TOKEN[1]: []" in stdout
        assert "TOKEN[2]: [b]" in stdout


# ---- fail_to_pass ----

class TestFailToPass:

    @pytest.mark.fail_to_pass
    def test_escaped_delimiter(self, tokenizer_binary):
        r"""hello\,world,foo should split into ["hello,world", "foo"]."""
        stdout, stderr, rc = run_binary(tokenizer_binary, args=['escaped_delimiter'])
        assert rc == 0, f"Crashed: {stderr}"
        assert "COUNT: 2" in stdout, f"Expected 2 tokens, got: {stdout}"
        assert "TOKEN[0]: [hello,world]" in stdout, f"Escape not resolved: {stdout}"
        assert "TOKEN[1]: [foo]" in stdout

    @pytest.mark.fail_to_pass
    def test_quoted_string(self, tokenizer_binary):
        """'"a,b",c' should split into ["a,b", "c"]."""
        stdout, stderr, rc = run_binary(tokenizer_binary, args=['quoted_string'])
        assert rc == 0, f"Crashed: {stderr}"
        assert "COUNT: 2" in stdout, f"Expected 2 tokens, got: {stdout}"
        assert "TOKEN[0]: [a,b]" in stdout, f"Quotes not handled: {stdout}"
        assert "TOKEN[1]: [c]" in stdout

    @pytest.mark.fail_to_pass
    def test_escaped_backslash(self, tokenizer_binary):
        r"""hello\\,world should split into ["hello\", "world"]."""
        stdout, stderr, rc = run_binary(tokenizer_binary, args=['escaped_backslash'])
        assert rc == 0, f"Crashed: {stderr}"
        assert "COUNT: 2" in stdout, f"Expected 2 tokens, got: {stdout}"
        assert "TOKEN[0]: [hello\\]" in stdout, f"Double backslash not handled: {stdout}"
        assert "TOKEN[1]: [world]" in stdout

    @pytest.mark.fail_to_pass
    def test_mixed_quoting_and_escaping(self, tokenizer_binary):
        r""""x,y",a\,b,c should produce ["x,y", "a,b", "c"]."""
        stdout, stderr, rc = run_binary(tokenizer_binary, args=['mixed'])
        assert rc == 0, f"Crashed: {stderr}"
        assert "COUNT: 3" in stdout, f"Expected 3 tokens, got: {stdout}"
        assert "TOKEN[0]: [x,y]" in stdout
        assert "TOKEN[1]: [a,b]" in stdout
        assert "TOKEN[2]: [c]" in stdout
