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
    """Parse the structured output from the spmv binary."""
    info = {}
    for line in stdout.splitlines():
        m = re.match(r'^([A-Z_]+)=(.+)$', line)
        if m:
            key = m.group(1)
            val = m.group(2)
            try:
                if '.' in val or 'e' in val.lower():
                    info[key] = float(val)
                else:
                    info[key] = int(val)
            except ValueError:
                info[key] = val
    return info


skip_no_nvcc = pytest.mark.skipif(not has_nvcc(), reason="nvcc not available or not working")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@skip_no_nvcc
class TestSparseMatVecMultiply:
    """Tests for CUDA CSR sparse matrix-vector multiply."""

    @pytest.fixture(autouse=True)
    def _compile(self):
        self.binary = compile_cuda(['spmv.cu'], 'spmv')

    # --- fail_to_pass -------------------------------------------------------

    @pytest.mark.fail_to_pass
    def test_spmv_identity_4x4(self):
        """4×4 identity matrix — y should equal x."""
        stdout, _, rc = run_binary(
            self.binary, ['--size', '4', '--mode', 'identity', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('MODE') == 'identity'
        assert info.get('MATCH') == 1, (
            f"Mismatches: {info.get('MISMATCHES')}, "
            f"first bad row {info.get('FIRST_BAD_ROW')}: "
            f"expected {info.get('EXPECTED')}, got {info.get('GOT')}")

    @pytest.mark.fail_to_pass
    def test_spmv_random_100x100(self):
        """100×100 random sparse matrix, ~10% density."""
        stdout, _, rc = run_binary(
            self.binary, ['--size', '100', '--mode', 'random', '--density', '0.1', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, (
            f"Mismatches: {info.get('MISMATCHES')}, max_rel_err={info.get('MAX_REL_ERR')}")

    @pytest.mark.fail_to_pass
    def test_spmv_empty_rows(self):
        """Matrix with every other row empty — tests empty-row handling."""
        stdout, _, rc = run_binary(
            self.binary, ['--size', '50', '--mode', 'empty', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('MODE') == 'empty'
        assert info.get('MATCH') == 1, (
            f"Mismatches: {info.get('MISMATCHES')}, "
            f"first bad row {info.get('FIRST_BAD_ROW')}: "
            f"expected {info.get('EXPECTED')}, got {info.get('GOT')}")

    @pytest.mark.fail_to_pass
    def test_spmv_random_1000x1000(self):
        """1000×1000 random sparse matrix."""
        stdout, _, rc = run_binary(
            self.binary, ['--size', '1000', '--mode', 'random', '--density', '0.05', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, (
            f"Mismatches: {info.get('MISMATCHES')}, max_rel_err={info.get('MAX_REL_ERR')}")

    # --- pass_to_pass -------------------------------------------------------

    def test_compilation_succeeds(self):
        """The source must compile without errors."""
        assert os.path.isfile(self.binary)

    def test_output_format(self):
        """Binary should produce parseable output."""
        stdout, _, rc = run_binary(
            self.binary, ['--size', '4', '--mode', 'identity', '--seed', '1'])
        info = parse_output(stdout)
        assert 'SIZE' in info
        assert 'NNZ' in info
        assert 'MATCH' in info
