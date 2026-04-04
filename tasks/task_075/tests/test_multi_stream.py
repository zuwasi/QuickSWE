import subprocess
import os
import tempfile
import platform
import shutil
import re

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def compile_cuda(src_files, output_name, extra_flags=None):
    """Compile CUDA files with nvcc."""
    src_dir = os.path.join(os.path.dirname(__file__), '..', 'src')
    sources = [os.path.join(src_dir, f) for f in src_files]
    tmp = tempfile.mkdtemp()
    ext = '.exe' if platform.system() == 'Windows' else ''
    out_path = os.path.join(tmp, output_name + ext)
    cmd = ['nvcc'] + sources + ['-o', out_path]
    if extra_flags:
        cmd.extend(extra_flags)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(f"CUDA compilation failed:\n{result.stderr}")
    return out_path


def run_binary(path, args=None):
    """Run a compiled binary and return (stdout, stderr, returncode)."""
    cmd = [path] + (args or [])
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return result.stdout, result.stderr, result.returncode


def has_nvcc():
    """Check that nvcc is available AND can actually compile."""
    if shutil.which('nvcc') is None:
        return False
    try:
        tmp = tempfile.mkdtemp()
        src = os.path.join(tmp, 'test.cu')
        with open(src, 'w') as f:
            f.write('int main(){return 0;}\n')
        ext = '.exe' if platform.system() == 'Windows' else ''
        out = os.path.join(tmp, 'test' + ext)
        r = subprocess.run(['nvcc', src, '-o', out],
                           capture_output=True, text=True, timeout=60)
        return r.returncode == 0
    except Exception:
        return False


def parse_output(stdout):
    """Parse KEY=VALUE output."""
    info = {}
    for line in stdout.splitlines():
        m = re.match(r'^([A-Z_]+)=([\d.eE+\-]+)$', line)
        if m:
            key = m.group(1)
            val = m.group(2)
            if '.' in val or 'e' in val.lower():
                info[key] = float(val)
            else:
                info[key] = int(val)
    return info


skip_no_nvcc = pytest.mark.skipif(not has_nvcc(), reason="nvcc not available or not working")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@skip_no_nvcc
class TestMultiStream:
    """Tests for multi-stream partitioned processing."""

    @pytest.fixture(autouse=True)
    def _compile(self):
        self.binary = compile_cuda(['multi_stream.cu'], 'multi_stream')

    # --- fail_to_pass -------------------------------------------------------

    @pytest.mark.fail_to_pass
    def test_even_size_1024(self):
        """N=1024: even split — overlap at midpoint causes duplicate."""
        stdout, _, rc = run_binary(self.binary, ['--size', '1024', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('SIZE') == 1024
        assert info.get('MATCH') == 1, (
            f"MISMATCHES={info.get('MISMATCHES')}, "
            f"DUPLICATES={info.get('DUPLICATES')}, "
            f"GARBAGE={info.get('GARBAGE')}")

    @pytest.mark.fail_to_pass
    def test_odd_size_1001(self):
        """N=1001: odd size — overlap + wrong copy-back size."""
        stdout, _, rc = run_binary(self.binary, ['--size', '1001', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, (
            f"MISMATCHES={info.get('MISMATCHES')}, "
            f"DUPLICATES={info.get('DUPLICATES')}")

    @pytest.mark.fail_to_pass
    def test_small_size_10(self):
        """N=10: very small — boundary bug is easy to spot."""
        stdout, _, rc = run_binary(self.binary, ['--size', '10', '--seed', '7'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, (
            f"MISMATCHES={info.get('MISMATCHES')}")

    @pytest.mark.fail_to_pass
    def test_large_size_8000(self):
        """N=8000: larger array stresses sync bug."""
        stdout, _, rc = run_binary(self.binary, ['--size', '8000', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, (
            f"MISMATCHES={info.get('MISMATCHES')}, "
            f"GARBAGE={info.get('GARBAGE')}")

    @pytest.mark.fail_to_pass
    def test_no_garbage_values(self):
        """N=500: no garbage (uninitialised) values should appear."""
        stdout, _, rc = run_binary(self.binary, ['--size', '500', '--seed', '7'])
        info = parse_output(stdout)
        assert info.get('GARBAGE', 0) == 0, (
            f"Garbage values detected: {info.get('GARBAGE')}")
        assert info.get('MATCH') == 1

    @pytest.mark.fail_to_pass
    def test_no_duplicates(self):
        """N=2000: no duplicate values near partition boundary."""
        stdout, _, rc = run_binary(self.binary, ['--size', '2000', '--seed', '99'])
        info = parse_output(stdout)
        assert info.get('DUPLICATES', 0) == 0, (
            f"Duplicates detected: {info.get('DUPLICATES')}")
        assert info.get('MATCH') == 1

    # --- pass_to_pass -------------------------------------------------------

    def test_compilation_succeeds(self):
        """Source must compile without errors."""
        assert os.path.isfile(self.binary)

    def test_output_format(self):
        """Binary should produce parseable output."""
        stdout, _, rc = run_binary(self.binary, ['--size', '64', '--seed', '1'])
        info = parse_output(stdout)
        assert 'SIZE' in info
        assert 'MISMATCHES' in info
        assert 'MATCH' in info
