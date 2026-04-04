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
class TestKNNSearch:
    """Tests for CUDA k-NN search with max-heap selection."""

    @pytest.fixture(autouse=True)
    def _compile(self):
        self.binary = compile_cuda(['knn_search.cu'], 'knn_search')

    # --- fail_to_pass -------------------------------------------------------

    @pytest.mark.fail_to_pass
    def test_knn_k1_small(self):
        """k=1 nearest neighbor, 100 dataset points."""
        stdout, _, rc = run_binary(self.binary,
            ['--queries', '20', '--dataset', '100', '--k', '1', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, (
            f"Index mismatches={info.get('INDEX_MISMATCHES')}, "
            f"Dist mismatches={info.get('DIST_MISMATCHES')}")

    @pytest.mark.fail_to_pass
    def test_knn_k5_medium(self):
        """k=5, 500 dataset points."""
        stdout, _, rc = run_binary(self.binary,
            ['--queries', '30', '--dataset', '500', '--k', '5', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, (
            f"Index mismatches={info.get('INDEX_MISMATCHES')}, "
            f"Dist mismatches={info.get('DIST_MISMATCHES')}")

    @pytest.mark.fail_to_pass
    def test_knn_k10_large(self):
        """k=10, 1000 dataset points."""
        stdout, _, rc = run_binary(self.binary,
            ['--queries', '50', '--dataset', '1000', '--k', '10', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, (
            f"Index mismatches={info.get('INDEX_MISMATCHES')}, "
            f"Dist mismatches={info.get('DIST_MISMATCHES')}")

    @pytest.mark.fail_to_pass
    def test_knn_k5_2000(self):
        """k=5, 2000 dataset points — larger scale."""
        stdout, _, rc = run_binary(self.binary,
            ['--queries', '50', '--dataset', '2000', '--k', '5', '--seed', '99'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, (
            f"Index mismatches={info.get('INDEX_MISMATCHES')}")

    @pytest.mark.fail_to_pass
    def test_knn_k10_small_dataset(self):
        """k=10, only 100 dataset points — tests different seed."""
        stdout, _, rc = run_binary(self.binary,
            ['--queries', '25', '--dataset', '100', '--k', '10', '--seed', '77'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1

    @pytest.mark.fail_to_pass
    def test_knn_k_exceeds_dataset(self):
        """k=20 but only 5 dataset points — padding required."""
        stdout, _, rc = run_binary(self.binary,
            ['--queries', '10', '--dataset', '5', '--k', '20', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('PADDING_OK') == 1, "Padding for k > n_dataset failed"
        assert info.get('MATCH') == 1

    # --- pass_to_pass -------------------------------------------------------

    def test_compilation_succeeds(self):
        """The source must compile without errors."""
        assert os.path.isfile(self.binary)

    def test_output_format(self):
        """Binary should produce parseable output."""
        stdout, _, rc = run_binary(self.binary,
            ['--queries', '5', '--dataset', '10', '--k', '3', '--seed', '1'])
        info = parse_output(stdout)
        assert 'N_QUERIES' in info
        assert 'K' in info
        assert 'MATCH' in info

    def test_cpu_knn_works(self):
        """CPU reference should produce consistent output."""
        stdout, _, rc = run_binary(self.binary,
            ['--queries', '5', '--dataset', '20', '--k', '3', '--seed', '1'])
        info = parse_output(stdout)
        assert 'INDEX_MISMATCHES' in info
