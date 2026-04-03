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
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return result.stdout, result.stderr, result.returncode


def has_nvcc():
    """Check that nvcc is available AND can actually compile (host compiler present)."""
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
    """Parse the structured output from vector_add binary."""
    info = {}
    results = {}
    for line in stdout.splitlines():
        m_info = re.match(r'^(SIZE|ERRORS)=(\d+)$', line)
        if m_info:
            info[m_info.group(1)] = int(m_info.group(2))
            continue
        m_res = re.match(r'^RESULT\[(\d+)\]=([\d.e+\-]+)$', line)
        if m_res:
            results[int(m_res.group(1))] = float(m_res.group(2))
    return info, results


# ---------------------------------------------------------------------------
# Skip all tests in this module if nvcc is not available
# ---------------------------------------------------------------------------
pytestmark = pytest.mark.skipif(not has_nvcc(), reason="nvcc not found")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestVectorAddBugFix:
    """Tests for the grid-dimension / bounds-check bug in vector_add.cu."""

    @pytest.fixture(autouse=True)
    def _compile(self, tmp_path):
        """Compile the CUDA source once per test class."""
        self.binary = compile_cuda(['vector_add.cu'], 'vector_add')

    # --- fail_to_pass: non-power-of-2 size ---------------------------------

    @pytest.mark.fail_to_pass
    def test_non_power_of_2_size_1000(self):
        """N=1000 is NOT divisible by BLOCK_SIZE=256.

        Before the fix the last 232 elements (768-999) are wrong.
        """
        stdout, stderr, rc = run_binary(self.binary, ['--size', '1000'])
        info, results = parse_output(stdout)

        assert info.get('SIZE') == 1000, f"Unexpected SIZE in output: {info}"
        assert info.get('ERRORS') == 0, (
            f"Kernel produced {info.get('ERRORS')} incorrect elements for N=1000"
        )

        # Spot-check a few trailing elements that are affected by the bug
        for i in [768, 900, 999]:
            expected = float(i + i * 2)
            actual = results.get(i)
            assert actual == pytest.approx(expected, abs=0.1), (
                f"RESULT[{i}] = {actual}, expected {expected}"
            )

    @pytest.mark.fail_to_pass
    def test_non_power_of_2_size_500(self):
        """N=500: another non-divisible size. Elements 256-499 must be correct."""
        stdout, stderr, rc = run_binary(self.binary, ['--size', '500'])
        info, results = parse_output(stdout)

        assert info.get('ERRORS') == 0, (
            f"Kernel produced {info.get('ERRORS')} incorrect elements for N=500"
        )

        for i in [256, 400, 499]:
            expected = float(i + i * 2)
            actual = results.get(i)
            assert actual == pytest.approx(expected, abs=0.1), (
                f"RESULT[{i}] = {actual}, expected {expected}"
            )

    # --- pass_to_pass: exact multiple of BLOCK_SIZE -------------------------

    def test_exact_multiple_256(self):
        """N=256 is an exact multiple of BLOCK_SIZE — should always work."""
        stdout, stderr, rc = run_binary(self.binary, ['--size', '256'])
        info, results = parse_output(stdout)

        assert info.get('SIZE') == 256
        assert info.get('ERRORS') == 0, (
            f"Kernel produced {info.get('ERRORS')} incorrect elements for N=256"
        )

    def test_exact_multiple_512(self):
        """N=512: another exact multiple."""
        stdout, stderr, rc = run_binary(self.binary, ['--size', '512'])
        info, results = parse_output(stdout)

        assert info.get('ERRORS') == 0
