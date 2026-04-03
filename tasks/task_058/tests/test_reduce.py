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
    """Parse the structured output from reduce binary."""
    info = {}
    for line in stdout.splitlines():
        m = re.match(r'^([A-Z_]+)=([\d.eE+\-]+)$', line)
        if m:
            key = m.group(1)
            val = m.group(2)
            if key in ('SIZE', 'MATCH'):
                info[key] = int(val)
            else:
                info[key] = float(val)
    return info


# ---------------------------------------------------------------------------
# Skip all tests in this module if nvcc is not available
# ---------------------------------------------------------------------------
pytestmark = pytest.mark.skipif(not has_nvcc(), reason="nvcc not found")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestParallelReduction:
    """Tests for the CUDA parallel reduction feature in reduce.cu."""

    @pytest.fixture(autouse=True)
    def _compile(self):
        self.binary = compile_cuda(['reduce.cu'], 'reduce')

    # --- fail_to_pass: gpu_reduce_sum must return correct results -----------

    @pytest.mark.fail_to_pass
    def test_reduce_n_1000(self):
        """N=1000: arbitrary size, not a power of 2."""
        stdout, _, rc = run_binary(self.binary, ['--size', '1000', '--seed', '42'])
        info = parse_output(stdout)

        assert info.get('SIZE') == 1000
        assert info.get('MATCH') == 1, (
            f"GPU sum ({info.get('GPU_SUM')}) does not match CPU sum "
            f"({info.get('CPU_SUM')}), rel_err={info.get('REL_ERR')}"
        )

    @pytest.mark.fail_to_pass
    def test_reduce_n_1023(self):
        """N=1023: one less than a power of 2."""
        stdout, _, rc = run_binary(self.binary, ['--size', '1023', '--seed', '42'])
        info = parse_output(stdout)

        assert info.get('MATCH') == 1, (
            f"GPU sum wrong for N=1023: gpu={info.get('GPU_SUM')}, "
            f"cpu={info.get('CPU_SUM')}"
        )

    @pytest.mark.fail_to_pass
    def test_reduce_n_1024(self):
        """N=1024: exact power of 2."""
        stdout, _, rc = run_binary(self.binary, ['--size', '1024', '--seed', '42'])
        info = parse_output(stdout)

        assert info.get('MATCH') == 1, (
            f"GPU sum wrong for N=1024: gpu={info.get('GPU_SUM')}, "
            f"cpu={info.get('CPU_SUM')}"
        )

    @pytest.mark.fail_to_pass
    def test_reduce_n_100000(self):
        """N=100000: large array."""
        stdout, _, rc = run_binary(self.binary, ['--size', '100000', '--seed', '42'])
        info = parse_output(stdout)

        assert info.get('MATCH') == 1, (
            f"GPU sum wrong for N=100000: gpu={info.get('GPU_SUM')}, "
            f"cpu={info.get('CPU_SUM')}, rel_err={info.get('REL_ERR')}"
        )

    @pytest.mark.fail_to_pass
    def test_reduce_performance_large_array(self):
        """For N=100000 the GPU reduction should be faster than CPU."""
        stdout, _, rc = run_binary(
            self.binary, ['--size', '100000', '--seed', '42', '--benchmark']
        )
        info = parse_output(stdout)

        assert info.get('MATCH') == 1, "GPU result must be correct first"

        gpu_ms = info.get('GPU_TIME_MS')
        cpu_ms = info.get('CPU_TIME_MS')
        assert gpu_ms is not None and cpu_ms is not None, (
            f"Benchmark timing missing: gpu={gpu_ms}, cpu={cpu_ms}"
        )
        assert gpu_ms < cpu_ms, (
            f"GPU ({gpu_ms:.4f} ms) should be faster than CPU ({cpu_ms:.4f} ms)"
        )

    # --- pass_to_pass: CPU function must still work -------------------------

    def test_cpu_reduce_still_works(self):
        """cpu_reduce_sum should remain correct regardless of GPU changes."""
        stdout, _, rc = run_binary(self.binary, ['--size', '1024', '--seed', '99'])
        info = parse_output(stdout)

        # CPU_SUM should be a positive number (all values are non-negative)
        assert info.get('CPU_SUM', 0) > 0, (
            f"CPU sum should be positive, got {info.get('CPU_SUM')}"
        )

    def test_compilation_succeeds(self):
        """The source must compile without errors."""
        assert os.path.isfile(self.binary)
