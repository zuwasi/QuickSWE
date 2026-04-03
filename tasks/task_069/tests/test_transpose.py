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
    """Parse the structured output from the transpose binary."""
    info = {}
    for line in stdout.splitlines():
        m = re.match(r'^([A-Z_]+)=([\d.eE+\-]+)$', line)
        if m:
            key = m.group(1)
            val = m.group(2)
            if key in ('ROWS', 'COLS', 'TOTAL_ELEMENTS', 'MISMATCHES', 'MATCH'):
                info[key] = int(val)
            else:
                info[key] = float(val)
    return info


skip_no_nvcc = pytest.mark.skipif(not has_nvcc(), reason="nvcc not available or not working")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@skip_no_nvcc
class TestMatrixTranspose:
    """Tests for CUDA tiled matrix transpose with shared memory."""

    @pytest.fixture(autouse=True)
    def _compile(self):
        self.binary = compile_cuda(['transpose.cu'], 'transpose')

    # --- fail_to_pass -------------------------------------------------------

    @pytest.mark.fail_to_pass
    def test_transpose_64x128(self):
        """Non-square: 64 rows × 128 cols."""
        stdout, _, rc = run_binary(self.binary, ['--rows', '64', '--cols', '128', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('ROWS') == 64
        assert info.get('COLS') == 128
        assert info.get('MATCH') == 1, f"Mismatches: {info.get('MISMATCHES')}"

    @pytest.mark.fail_to_pass
    def test_transpose_128x64(self):
        """Non-square: 128 rows × 64 cols."""
        stdout, _, rc = run_binary(self.binary, ['--rows', '128', '--cols', '64', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, f"Mismatches: {info.get('MISMATCHES')}"

    @pytest.mark.fail_to_pass
    def test_transpose_100x200(self):
        """Non-square, non-tile-aligned: 100×200."""
        stdout, _, rc = run_binary(self.binary, ['--rows', '100', '--cols', '200', '--seed', '7'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, f"Mismatches: {info.get('MISMATCHES')}"

    @pytest.mark.fail_to_pass
    def test_transpose_256x256(self):
        """Square: 256×256."""
        stdout, _, rc = run_binary(self.binary, ['--rows', '256', '--cols', '256', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, f"Mismatches: {info.get('MISMATCHES')}"

    @pytest.mark.fail_to_pass
    def test_transpose_1x1024(self):
        """Degenerate non-square: single row, 1024 cols."""
        stdout, _, rc = run_binary(self.binary, ['--rows', '1', '--cols', '1024', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, f"Mismatches: {info.get('MISMATCHES')}"

    # --- pass_to_pass -------------------------------------------------------

    def test_compilation_succeeds(self):
        """The source must compile without errors."""
        assert os.path.isfile(self.binary)

    def test_cpu_transpose_correct(self):
        """CPU reference transpose still works."""
        stdout, _, rc = run_binary(self.binary, ['--rows', '4', '--cols', '8', '--seed', '1'])
        info = parse_output(stdout)
        assert info.get('ROWS') == 4
        assert info.get('COLS') == 8
