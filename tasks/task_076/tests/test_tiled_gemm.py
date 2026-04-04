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
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
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
        # Also capture string values like MODE=TILED
        m2 = re.match(r'^([A-Z_]+)=([A-Za-z]+)$', line)
        if m2:
            info[m2.group(1)] = m2.group(2)
    return info


skip_no_nvcc = pytest.mark.skipif(not has_nvcc(), reason="nvcc not available or not working")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@skip_no_nvcc
class TestTiledGemm:
    """Tests for tiled GEMM with register blocking."""

    @pytest.fixture(autouse=True)
    def _compile(self):
        self.binary = compile_cuda(['tiled_gemm.cu'], 'tiled_gemm')

    # --- fail_to_pass -------------------------------------------------------

    @pytest.mark.fail_to_pass
    def test_square_64(self):
        """64x64 * 64x64: tile-aligned square matrix."""
        stdout, _, rc = run_binary(self.binary,
            ['--M', '64', '--N', '64', '--K', '64', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('MODE') == 'TILED'
        assert info.get('MATCH') == 1, (
            f"MAX_ERROR={info.get('MAX_ERROR')}, MISMATCHES={info.get('MISMATCHES')}")

    @pytest.mark.fail_to_pass
    def test_square_100(self):
        """100x100 * 100x100: non-tile-aligned square matrix."""
        stdout, _, rc = run_binary(self.binary,
            ['--M', '100', '--N', '100', '--K', '100', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, (
            f"MAX_ERROR={info.get('MAX_ERROR')}, MISMATCHES={info.get('MISMATCHES')}")

    @pytest.mark.fail_to_pass
    def test_rect_256x128(self):
        """256x128 * 128x256: rectangular matrices."""
        stdout, _, rc = run_binary(self.binary,
            ['--M', '256', '--N', '256', '--K', '128', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, (
            f"MAX_ERROR={info.get('MAX_ERROR')}, MISMATCHES={info.get('MISMATCHES')}")

    @pytest.mark.fail_to_pass
    def test_rect_500x300(self):
        """500x300 * 300x400: large non-aligned rectangular matrices."""
        stdout, _, rc = run_binary(self.binary,
            ['--M', '500', '--N', '400', '--K', '300', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, (
            f"MAX_ERROR={info.get('MAX_ERROR')}, MISMATCHES={info.get('MISMATCHES')}")

    @pytest.mark.fail_to_pass
    def test_max_error_within_tolerance(self):
        """Max element-wise error must be below 1e-2."""
        stdout, _, rc = run_binary(self.binary,
            ['--M', '100', '--N', '100', '--K', '100', '--seed', '99'])
        info = parse_output(stdout)
        max_err = info.get('MAX_ERROR', 999.0)
        assert max_err < 1e-2, f"MAX_ERROR={max_err} exceeds tolerance"

    @pytest.mark.fail_to_pass
    def test_small_non_aligned_17x13(self):
        """17x13 * 13x19: very small non-aligned dimensions."""
        stdout, _, rc = run_binary(self.binary,
            ['--M', '17', '--N', '19', '--K', '13', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, (
            f"MAX_ERROR={info.get('MAX_ERROR')}, MISMATCHES={info.get('MISMATCHES')}")

    # --- pass_to_pass -------------------------------------------------------

    def test_compilation_succeeds(self):
        """Source must compile without errors."""
        assert os.path.isfile(self.binary)

    def test_naive_still_works(self):
        """Naive kernel should remain functional."""
        stdout, _, rc = run_binary(self.binary,
            ['--M', '32', '--N', '32', '--K', '32', '--seed', '1', '--naive'])
        info = parse_output(stdout)
        assert info.get('MODE') == 'NAIVE'
        assert info.get('MATCH') == 1

    def test_output_format(self):
        """Binary should produce parseable output."""
        stdout, _, rc = run_binary(self.binary,
            ['--M', '8', '--N', '8', '--K', '8', '--seed', '1'])
        info = parse_output(stdout)
        assert 'M' in info
        assert 'N' in info
        assert 'K' in info
        assert 'MATCH' in info
        assert 'MAX_ERROR' in info
