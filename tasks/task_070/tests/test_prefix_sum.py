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
    """Parse the structured output from the prefix_sum binary."""
    info = {}
    for line in stdout.splitlines():
        m = re.match(r'^([A-Z_]+)=([\d.eE+\-]+)$', line)
        if m:
            key = m.group(1)
            val = m.group(2)
            info[key] = int(val) if '.' not in val and 'e' not in val.lower() else float(val)
    return info


skip_no_nvcc = pytest.mark.skipif(not has_nvcc(), reason="nvcc not available or not working")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@skip_no_nvcc
class TestPrefixSum:
    """Tests for CUDA Blelloch parallel prefix sum."""

    @pytest.fixture(autouse=True)
    def _compile(self):
        self.binary = compile_cuda(['prefix_sum.cu'], 'prefix_sum')

    # --- fail_to_pass -------------------------------------------------------

    @pytest.mark.fail_to_pass
    def test_scan_n_128(self):
        """N=128: fits within a single block (2*BLOCK_SIZE=512 elements)."""
        stdout, _, rc = run_binary(self.binary, ['--size', '128', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('SIZE') == 128
        assert info.get('MATCH') == 1, (
            f"Mismatches: {info.get('MISMATCHES')}, "
            f"first bad at index {info.get('FIRST_BAD_INDEX')}: "
            f"expected {info.get('EXPECTED')}, got {info.get('GOT')}"
        )

    @pytest.mark.fail_to_pass
    def test_scan_n_1000(self):
        """N=1000: spans multiple blocks, arbitrary size."""
        stdout, _, rc = run_binary(self.binary, ['--size', '1000', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('SIZE') == 1000
        assert info.get('MATCH') == 1, (
            f"Mismatches: {info.get('MISMATCHES')}, "
            f"first bad at index {info.get('FIRST_BAD_INDEX')}: "
            f"expected {info.get('EXPECTED')}, got {info.get('GOT')}"
        )

    @pytest.mark.fail_to_pass
    def test_scan_n_10000(self):
        """N=10000: many blocks."""
        stdout, _, rc = run_binary(self.binary, ['--size', '10000', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('SIZE') == 10000
        assert info.get('MATCH') == 1, (
            f"Mismatches: {info.get('MISMATCHES')}, "
            f"first bad at index {info.get('FIRST_BAD_INDEX')}: "
            f"expected {info.get('EXPECTED')}, got {info.get('GOT')}"
        )

    @pytest.mark.fail_to_pass
    def test_scan_n_512(self):
        """N=512: exactly one block (2*256)."""
        stdout, _, rc = run_binary(self.binary, ['--size', '512', '--seed', '7'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, (
            f"Mismatches: {info.get('MISMATCHES')}"
        )

    # --- pass_to_pass -------------------------------------------------------

    def test_compilation_succeeds(self):
        """The source must compile without errors."""
        assert os.path.isfile(self.binary)

    def test_output_format(self):
        """Binary should produce parseable output."""
        stdout, _, rc = run_binary(self.binary, ['--size', '16', '--seed', '1'])
        info = parse_output(stdout)
        assert 'SIZE' in info
        assert 'MISMATCHES' in info
        assert 'MATCH' in info
