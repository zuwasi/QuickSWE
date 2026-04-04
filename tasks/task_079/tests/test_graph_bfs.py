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
    return info


skip_no_nvcc = pytest.mark.skipif(not has_nvcc(), reason="nvcc not available or not working")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@skip_no_nvcc
class TestGraphBFS:
    """Tests for CUDA graph BFS."""

    @pytest.fixture(autouse=True)
    def _compile(self):
        self.binary = compile_cuda(['graph_bfs.cu'], 'graph_bfs')

    # --- fail_to_pass -------------------------------------------------------

    @pytest.mark.fail_to_pass
    def test_bfs_small_100(self):
        """100 nodes, 500 edges: basic correctness."""
        stdout, _, rc = run_binary(self.binary,
            ['--nodes', '100', '--edges', '500', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('NODES') == 100
        assert info.get('MATCH') == 1, (
            f"MISMATCHES={info.get('MISMATCHES')}, "
            f"WRONG_SHORTER={info.get('WRONG_SHORTER')}, "
            f"WRONG_LONGER={info.get('WRONG_LONGER')}")

    @pytest.mark.fail_to_pass
    def test_bfs_medium_1000(self):
        """1000 nodes, 5000 edges: medium graph."""
        stdout, _, rc = run_binary(self.binary,
            ['--nodes', '1000', '--edges', '5000', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, (
            f"MISMATCHES={info.get('MISMATCHES')}")

    @pytest.mark.fail_to_pass
    def test_bfs_sparse(self):
        """500 nodes, 600 edges: sparse graph (nearly a tree)."""
        stdout, _, rc = run_binary(self.binary,
            ['--nodes', '500', '--edges', '600', '--seed', '7'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, (
            f"MISMATCHES={info.get('MISMATCHES')}")

    @pytest.mark.fail_to_pass
    def test_bfs_dense(self):
        """200 nodes, 5000 edges: dense graph — many duplicate frontier entries."""
        stdout, _, rc = run_binary(self.binary,
            ['--nodes', '200', '--edges', '5000', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, (
            f"MISMATCHES={info.get('MISMATCHES')}")

    @pytest.mark.fail_to_pass
    def test_all_reachable(self):
        """All nodes should be reachable (graph is connected)."""
        stdout, _, rc = run_binary(self.binary,
            ['--nodes', '100', '--edges', '500', '--seed', '99'])
        info = parse_output(stdout)
        assert info.get('REACHABLE') == 100, (
            f"Only {info.get('REACHABLE')} of 100 nodes reachable")
        assert info.get('MATCH') == 1

    @pytest.mark.fail_to_pass
    def test_no_wrong_distances(self):
        """300 nodes: no distances should be shorter or longer than reference."""
        stdout, _, rc = run_binary(self.binary,
            ['--nodes', '300', '--edges', '1500', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('WRONG_SHORTER', -1) == 0, (
            f"WRONG_SHORTER={info.get('WRONG_SHORTER')}")
        assert info.get('WRONG_LONGER', -1) == 0, (
            f"WRONG_LONGER={info.get('WRONG_LONGER')}")
        assert info.get('MATCH') == 1

    # --- pass_to_pass -------------------------------------------------------

    def test_compilation_succeeds(self):
        """Source must compile without errors."""
        assert os.path.isfile(self.binary)

    def test_output_format(self):
        """Binary should produce parseable output."""
        stdout, _, rc = run_binary(self.binary,
            ['--nodes', '10', '--edges', '20', '--seed', '1'])
        info = parse_output(stdout)
        assert 'NODES' in info
        assert 'MISMATCHES' in info
        assert 'REACHABLE' in info
        assert 'MATCH' in info
