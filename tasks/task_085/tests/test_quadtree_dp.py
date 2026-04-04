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
    cmd = ['nvcc'] + sources + ['-o', out_path, '-rdc=true', '-lcudadevrt', '-lm']
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
class TestQuadtreeDP:
    """Tests for CUDA dynamic parallelism quadtree processing."""

    @pytest.fixture(autouse=True)
    def _compile(self):
        self.binary = compile_cuda(['quadtree_dp.cu'], 'quadtree_dp')

    # --- fail_to_pass -------------------------------------------------------

    @pytest.mark.fail_to_pass
    def test_depth1_serial(self):
        """Shallow tree (depth 1), serial mode."""
        stdout, _, rc = run_binary(self.binary,
            ['--depth', '1', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, (
            f"Mismatches={info.get('MISMATCHES')}, "
            f"CPU root={info.get('CPU_ROOT')}, GPU root={info.get('GPU_ROOT')}")

    @pytest.mark.fail_to_pass
    def test_depth2_serial(self):
        """Medium tree (depth 2), serial mode."""
        stdout, _, rc = run_binary(self.binary,
            ['--depth', '2', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, (
            f"Mismatches={info.get('MISMATCHES')}, "
            f"Root error={info.get('ROOT_ERROR')}")

    @pytest.mark.fail_to_pass
    def test_depth3_serial(self):
        """Deeper tree (depth 3) — likely to expose synchronization bugs."""
        stdout, _, rc = run_binary(self.binary,
            ['--depth', '3', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, (
            f"Mismatches={info.get('MISMATCHES')}, "
            f"Max error={info.get('MAX_ERROR')}")

    @pytest.mark.fail_to_pass
    def test_depth2_parallel(self):
        """Depth 2 with parallel level processing — tests concurrent parent issue."""
        stdout, _, rc = run_binary(self.binary,
            ['--depth', '2', '--seed', '42', '--parallel'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, (
            f"Mismatches={info.get('MISMATCHES')}, "
            f"Root error={info.get('ROOT_ERROR')}")

    @pytest.mark.fail_to_pass
    def test_depth3_parallel(self):
        """Depth 3 parallel — high deadlock risk."""
        stdout, _, rc = run_binary(self.binary,
            ['--depth', '3', '--seed', '99', '--parallel'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1

    @pytest.mark.fail_to_pass
    def test_root_aggregation(self):
        """Root value should equal sum of all leaf values."""
        stdout, _, rc = run_binary(self.binary,
            ['--depth', '3', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('ROOT_OK') == 1, (
            f"Root error={info.get('ROOT_ERROR')}, "
            f"CPU={info.get('CPU_ROOT')}, GPU={info.get('GPU_ROOT')}")

    @pytest.mark.fail_to_pass
    def test_different_seed(self):
        """Different tree structure to cover more cases."""
        stdout, _, rc = run_binary(self.binary,
            ['--depth', '3', '--seed', '777'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1

    # --- pass_to_pass -------------------------------------------------------

    def test_compilation_succeeds(self):
        """The source must compile with -rdc=true -lcudadevrt."""
        assert os.path.isfile(self.binary)

    def test_output_format(self):
        """Binary should produce parseable output."""
        stdout, _, rc = run_binary(self.binary,
            ['--depth', '1', '--seed', '1'])
        info = parse_output(stdout)
        assert 'DEPTH' in info
        assert 'NODES' in info
        assert 'MATCH' in info

    def test_cpu_reference_works(self):
        """CPU recursive processing should produce non-zero root."""
        stdout, _, rc = run_binary(self.binary,
            ['--depth', '2', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('CPU_ROOT', 0.0) > 0.0
