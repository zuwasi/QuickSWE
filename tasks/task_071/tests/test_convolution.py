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
    """Parse the structured output from the convolution binary."""
    info = {}
    for line in stdout.splitlines():
        # Handle string values like MODE=tiled
        m = re.match(r'^([A-Z_]+)=(.+)$', line)
        if m:
            key = m.group(1)
            val = m.group(2)
            try:
                if '.' in val or 'e' in val.lower():
                    info[key] = float(val)
                else:
                    info[key] = int(val)
            except ValueError:
                info[key] = val
    return info


skip_no_nvcc = pytest.mark.skipif(not has_nvcc(), reason="nvcc not available or not working")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@skip_no_nvcc
class TestTiledConvolution:
    """Tests for CUDA tiled 1D convolution with halo cells."""

    @pytest.fixture(autouse=True)
    def _compile(self):
        self.binary = compile_cuda(['convolution.cu'], 'convolution')

    # --- fail_to_pass: tiled kernel must produce correct results -------------

    @pytest.mark.fail_to_pass
    def test_tiled_filter3_n256(self):
        """Tiled convolution, filter_size=3, N=256."""
        stdout, _, rc = run_binary(
            self.binary, ['--size', '256', '--filter', '3', '--mode', 'tiled', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('FILTER_SIZE') == 3
        assert info.get('MATCH') == 1, (
            f"Mismatches: {info.get('MISMATCHES')}, max_rel_err={info.get('MAX_REL_ERR')}")

    @pytest.mark.fail_to_pass
    def test_tiled_filter5_n1000(self):
        """Tiled convolution, filter_size=5, N=1000."""
        stdout, _, rc = run_binary(
            self.binary, ['--size', '1000', '--filter', '5', '--mode', 'tiled', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, (
            f"Mismatches: {info.get('MISMATCHES')}, max_rel_err={info.get('MAX_REL_ERR')}")

    @pytest.mark.fail_to_pass
    def test_tiled_filter7_n10000(self):
        """Tiled convolution, filter_size=7, N=10000."""
        stdout, _, rc = run_binary(
            self.binary, ['--size', '10000', '--filter', '7', '--mode', 'tiled', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, (
            f"Mismatches: {info.get('MISMATCHES')}, max_rel_err={info.get('MAX_REL_ERR')}")

    @pytest.mark.fail_to_pass
    def test_tiled_filter5_n256(self):
        """Tiled convolution, filter_size=5, N=256 (tile-aligned)."""
        stdout, _, rc = run_binary(
            self.binary, ['--size', '256', '--filter', '5', '--mode', 'tiled', '--seed', '7'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, (
            f"Mismatches: {info.get('MISMATCHES')}")

    @pytest.mark.fail_to_pass
    def test_tiled_filter3_n10000(self):
        """Tiled convolution, filter_size=3, N=10000 (large + small filter)."""
        stdout, _, rc = run_binary(
            self.binary, ['--size', '10000', '--filter', '3', '--mode', 'tiled', '--seed', '99'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, (
            f"Mismatches: {info.get('MISMATCHES')}")

    # --- pass_to_pass: naive kernel and CPU must still work ------------------

    def test_compilation_succeeds(self):
        """The source must compile without errors."""
        assert os.path.isfile(self.binary)

    def test_naive_kernel_still_correct(self):
        """Naive GPU convolution should remain correct."""
        stdout, _, rc = run_binary(
            self.binary, ['--size', '256', '--filter', '5', '--mode', 'naive', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, (
            f"Naive kernel broken: mismatches={info.get('MISMATCHES')}")

    def test_output_format(self):
        """Binary should produce parseable output."""
        stdout, _, rc = run_binary(
            self.binary, ['--size', '16', '--filter', '3', '--mode', 'tiled', '--seed', '1'])
        info = parse_output(stdout)
        assert 'SIZE' in info
        assert 'FILTER_SIZE' in info
        assert 'MATCH' in info
