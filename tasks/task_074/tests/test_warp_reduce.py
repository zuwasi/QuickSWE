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
class TestWarpReduce:
    """Tests for warp-level shuffle reduction."""

    @pytest.fixture(autouse=True)
    def _compile(self):
        self.binary = compile_cuda(['warp_reduce.cu'], 'warp_reduce')

    # --- fail_to_pass -------------------------------------------------------

    @pytest.mark.fail_to_pass
    def test_reduce_n_1000(self):
        """N=1000: not a multiple of 32 — triggers mask/width bug."""
        stdout, _, rc = run_binary(self.binary, ['--size', '1000', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('SIZE') == 1000
        assert info.get('MATCH') == 1, (
            f"GPU_SUM={info.get('GPU_SUM')}, CPU_SUM={info.get('CPU_SUM')}, "
            f"ABSDIFF={info.get('ABSDIFF')}")

    @pytest.mark.fail_to_pass
    def test_reduce_n_100(self):
        """N=100: small non-aligned size."""
        stdout, _, rc = run_binary(self.binary, ['--size', '100', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, (
            f"GPU_SUM={info.get('GPU_SUM')}, CPU_SUM={info.get('CPU_SUM')}, "
            f"ABSDIFF={info.get('ABSDIFF')}")

    @pytest.mark.fail_to_pass
    def test_reduce_n_33(self):
        """N=33: just one more than a warp — minimal partial warp case."""
        stdout, _, rc = run_binary(self.binary, ['--size', '33', '--seed', '7'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, (
            f"GPU_SUM={info.get('GPU_SUM')}, CPU_SUM={info.get('CPU_SUM')}")

    @pytest.mark.fail_to_pass
    def test_reduce_n_4099(self):
        """N=4099: multi-block with partial last warp."""
        stdout, _, rc = run_binary(self.binary, ['--size', '4099', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, (
            f"GPU_SUM={info.get('GPU_SUM')}, CPU_SUM={info.get('CPU_SUM')}, "
            f"ABSDIFF={info.get('ABSDIFF')}")

    @pytest.mark.fail_to_pass
    def test_reduce_n_513(self):
        """N=513: two blocks with one partial thread."""
        stdout, _, rc = run_binary(self.binary, ['--size', '513', '--seed', '99'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, (
            f"ABSDIFF={info.get('ABSDIFF')}")

    # --- pass_to_pass -------------------------------------------------------

    def test_compilation_succeeds(self):
        """Source must compile without errors."""
        assert os.path.isfile(self.binary)

    def test_reduce_n_1024(self):
        """N=1024: aligned size should always work."""
        stdout, _, rc = run_binary(self.binary, ['--size', '1024', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1

    def test_reduce_n_2048(self):
        """N=2048: larger aligned size."""
        stdout, _, rc = run_binary(self.binary, ['--size', '2048', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1

    def test_output_format(self):
        """Binary should produce parseable output."""
        stdout, _, rc = run_binary(self.binary, ['--size', '32', '--seed', '1'])
        info = parse_output(stdout)
        assert 'SIZE' in info
        assert 'CPU_SUM' in info
        assert 'GPU_SUM' in info
        assert 'MATCH' in info
