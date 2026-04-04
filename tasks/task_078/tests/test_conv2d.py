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
class TestConv2D:
    """Tests for CUDA 2D image convolution."""

    @pytest.fixture(autouse=True)
    def _compile(self):
        self.binary = compile_cuda(['conv2d.cu'], 'conv2d')

    # --- fail_to_pass -------------------------------------------------------

    @pytest.mark.fail_to_pass
    def test_box_3x3_aligned(self):
        """64x64 image, 3x3 box blur — tile-aligned."""
        stdout, _, rc = run_binary(self.binary,
            ['--width', '64', '--height', '64', '--radius', '1',
             '--kernel', 'box', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, (
            f"MAX_ERROR={info.get('MAX_ERROR')}, "
            f"MISMATCHES={info.get('MISMATCHES')}, "
            f"BOUNDARY_ERRORS={info.get('BOUNDARY_ERRORS')}")

    @pytest.mark.fail_to_pass
    def test_box_3x3_non_aligned(self):
        """100x100 image, 3x3 box blur — non-tile-aligned."""
        stdout, _, rc = run_binary(self.binary,
            ['--width', '100', '--height', '100', '--radius', '1',
             '--kernel', 'box', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, (
            f"MAX_ERROR={info.get('MAX_ERROR')}, "
            f"MISMATCHES={info.get('MISMATCHES')}")

    @pytest.mark.fail_to_pass
    def test_gaussian_5x5(self):
        """64x64 image, 5x5 Gaussian — tests radius=2 consistency."""
        stdout, _, rc = run_binary(self.binary,
            ['--width', '64', '--height', '64', '--radius', '2',
             '--kernel', 'gaussian', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, (
            f"MAX_ERROR={info.get('MAX_ERROR')}, "
            f"MISMATCHES={info.get('MISMATCHES')}")

    @pytest.mark.fail_to_pass
    def test_gaussian_5x5_non_aligned(self):
        """50x75 image, 5x5 Gaussian — non-aligned + larger kernel."""
        stdout, _, rc = run_binary(self.binary,
            ['--width', '50', '--height', '75', '--radius', '2',
             '--kernel', 'gaussian', '--seed', '99'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, (
            f"MAX_ERROR={info.get('MAX_ERROR')}, "
            f"MISMATCHES={info.get('MISMATCHES')}")

    @pytest.mark.fail_to_pass
    def test_no_boundary_errors(self):
        """128x128, 3x3 box: no errors at tile boundaries."""
        stdout, _, rc = run_binary(self.binary,
            ['--width', '128', '--height', '128', '--radius', '1',
             '--kernel', 'box', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('BOUNDARY_ERRORS', -1) == 0, (
            f"BOUNDARY_ERRORS={info.get('BOUNDARY_ERRORS')}")

    @pytest.mark.fail_to_pass
    def test_small_image_7x7(self):
        """7x7 image, 3x3 box — smaller than one tile."""
        stdout, _, rc = run_binary(self.binary,
            ['--width', '7', '--height', '7', '--radius', '1',
             '--kernel', 'box', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, (
            f"MAX_ERROR={info.get('MAX_ERROR')}")

    # --- pass_to_pass -------------------------------------------------------

    def test_compilation_succeeds(self):
        """Source must compile without errors."""
        assert os.path.isfile(self.binary)

    def test_output_format(self):
        """Binary should produce parseable output."""
        stdout, _, rc = run_binary(self.binary,
            ['--width', '16', '--height', '16', '--radius', '1', '--seed', '1'])
        info = parse_output(stdout)
        assert 'WIDTH' in info
        assert 'HEIGHT' in info
        assert 'KSIZE' in info
        assert 'MATCH' in info
        assert 'MAX_ERROR' in info
