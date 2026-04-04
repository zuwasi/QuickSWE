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
    cmd = ['nvcc'] + sources + ['-o', out_path, '-lm']
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
    """Parse the structured output."""
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
class TestFFTButterfly:
    """Tests for CUDA FFT with butterfly operations."""

    @pytest.fixture(autouse=True)
    def _compile(self):
        self.binary = compile_cuda(['fft_butterfly.cu'], 'fft_butterfly')

    # --- fail_to_pass -------------------------------------------------------

    @pytest.mark.fail_to_pass
    def test_roundtrip_n16(self):
        """FFT then IFFT should reconstruct original for N=16."""
        stdout, _, rc = run_binary(self.binary,
            ['--mode', 'roundtrip', '--size', '16', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('ROUNDTRIP_OK') == 1, (
            f"GPU RMS error = {info.get('GPU_RMS')}")

    @pytest.mark.fail_to_pass
    def test_roundtrip_n256(self):
        """FFT roundtrip for N=256."""
        stdout, _, rc = run_binary(self.binary,
            ['--mode', 'roundtrip', '--size', '256', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('ROUNDTRIP_OK') == 1, (
            f"GPU RMS error = {info.get('GPU_RMS')}")

    @pytest.mark.fail_to_pass
    def test_roundtrip_n1024(self):
        """FFT roundtrip for N=1024 — error should not grow with size."""
        stdout, _, rc = run_binary(self.binary,
            ['--mode', 'roundtrip', '--size', '1024', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('ROUNDTRIP_OK') == 1, (
            f"GPU RMS error = {info.get('GPU_RMS')}")

    @pytest.mark.fail_to_pass
    def test_roundtrip_n4096(self):
        """FFT roundtrip for N=4096."""
        stdout, _, rc = run_binary(self.binary,
            ['--mode', 'roundtrip', '--size', '4096', '--seed', '99'])
        info = parse_output(stdout)
        assert info.get('ROUNDTRIP_OK') == 1, (
            f"GPU RMS error = {info.get('GPU_RMS')}")

    @pytest.mark.fail_to_pass
    def test_sine_peak_detection(self):
        """FFT of sine wave should produce spike at correct frequency bin."""
        stdout, _, rc = run_binary(self.binary,
            ['--mode', 'sine', '--size', '256', '--freq', '5'])
        info = parse_output(stdout)
        assert info.get('PEAK_OK') == 1, (
            f"GPU peak at bin {info.get('GPU_PEAK_BIN')}, "
            f"expected bin 5 or {256-5}")

    @pytest.mark.fail_to_pass
    def test_sine_magnitude_accuracy(self):
        """FFT magnitude spectrum should match CPU reference."""
        stdout, _, rc = run_binary(self.binary,
            ['--mode', 'sine', '--size', '512', '--freq', '10'])
        info = parse_output(stdout)
        assert info.get('MAG_OK') == 1, (
            f"Magnitude error = {info.get('MAG_ERROR')}")

    @pytest.mark.fail_to_pass
    def test_roundtrip_n8(self):
        """Small N=8 should work perfectly."""
        stdout, _, rc = run_binary(self.binary,
            ['--mode', 'roundtrip', '--size', '8', '--seed', '1'])
        info = parse_output(stdout)
        assert info.get('ROUNDTRIP_OK') == 1, (
            f"GPU RMS error = {info.get('GPU_RMS')}")

    # --- pass_to_pass -------------------------------------------------------

    def test_compilation_succeeds(self):
        """The source must compile without errors."""
        assert os.path.isfile(self.binary)

    def test_output_format_roundtrip(self):
        """Binary should produce parseable roundtrip output."""
        stdout, _, rc = run_binary(self.binary,
            ['--mode', 'roundtrip', '--size', '16', '--seed', '1'])
        info = parse_output(stdout)
        assert 'ROUNDTRIP_N' in info
        assert 'GPU_RMS' in info
        assert 'ROUNDTRIP_OK' in info

    def test_output_format_sine(self):
        """Binary should produce parseable sine output."""
        stdout, _, rc = run_binary(self.binary,
            ['--mode', 'sine', '--size', '64', '--freq', '3'])
        info = parse_output(stdout)
        assert 'SINE_N' in info
        assert 'GPU_PEAK_BIN' in info

    def test_cpu_roundtrip_correct(self):
        """CPU reference FFT roundtrip should be near-perfect."""
        stdout, _, rc = run_binary(self.binary,
            ['--mode', 'roundtrip', '--size', '256', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('CPU_RMS', 1.0) < 1e-4
