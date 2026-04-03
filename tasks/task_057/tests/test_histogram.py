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
    """Parse the structured output from histogram binary."""
    info = {}
    bins = {}
    for line in stdout.splitlines():
        m_info = re.match(r'^(SIZE|SEED|ERRORS)=(\d+)$', line)
        if m_info:
            info[m_info.group(1)] = int(m_info.group(2))
            continue
        m_bin = re.match(r'^BIN\[(\d+)\] gpu=(-?\d+) cpu=(-?\d+)$', line)
        if m_bin:
            idx = int(m_bin.group(1))
            bins[idx] = {
                'gpu': int(m_bin.group(2)),
                'cpu': int(m_bin.group(3)),
            }
    return info, bins


# ---------------------------------------------------------------------------
# Skip all tests in this module if nvcc is not available
# ---------------------------------------------------------------------------
pytestmark = pytest.mark.skipif(not has_nvcc(), reason="nvcc not found")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestHistogramBugFix:
    """Tests for the shared-memory race / init bug in histogram.cu."""

    @pytest.fixture(autouse=True)
    def _compile(self):
        self.binary = compile_cuda(['histogram.cu'], 'histogram')

    # --- fail_to_pass -------------------------------------------------------

    @pytest.mark.fail_to_pass
    def test_histogram_10000_elements(self):
        """With 10000 elements the uninitialised shared mem causes wrong bins."""
        stdout, stderr, rc = run_binary(
            self.binary, ['--size', '10000', '--seed', '42']
        )
        info, bins = parse_output(stdout)

        assert info.get('SIZE') == 10000
        assert info.get('ERRORS') == 0, (
            f"GPU histogram has {info.get('ERRORS')} mismatched bins out of 256"
        )

        # Verify every bin matches
        for idx in range(256):
            b = bins.get(idx, {})
            assert b.get('gpu') == b.get('cpu'), (
                f"BIN[{idx}]: gpu={b.get('gpu')} != cpu={b.get('cpu')}"
            )

    @pytest.mark.fail_to_pass
    def test_histogram_50000_elements(self):
        """Larger input amplifies the race condition."""
        stdout, stderr, rc = run_binary(
            self.binary, ['--size', '50000', '--seed', '123']
        )
        info, bins = parse_output(stdout)

        assert info.get('ERRORS') == 0, (
            f"GPU histogram has {info.get('ERRORS')} mismatched bins for N=50000"
        )

    # --- pass_to_pass -------------------------------------------------------

    def test_compilation_succeeds(self):
        """Compilation itself should always succeed (binary was built in fixture)."""
        assert os.path.isfile(self.binary)

    def test_trivial_single_element(self):
        """A single-element input should produce a histogram with exactly one
        non-zero bin."""
        stdout, stderr, rc = run_binary(
            self.binary, ['--size', '1', '--seed', '1']
        )
        info, bins = parse_output(stdout)

        assert info.get('SIZE') == 1

        # Exactly one bin should have count 1; the rest should be 0
        total_gpu = sum(b['gpu'] for b in bins.values())
        assert total_gpu == 1, f"Total GPU count should be 1, got {total_gpu}"
