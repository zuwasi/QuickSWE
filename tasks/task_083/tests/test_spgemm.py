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
class TestSpGEMM:
    """Tests for CUDA sparse matrix-matrix multiplication."""

    @pytest.fixture(autouse=True)
    def _compile(self):
        self.binary = compile_cuda(['spgemm.cu'], 'spgemm')

    # --- fail_to_pass -------------------------------------------------------

    @pytest.mark.fail_to_pass
    def test_random_sparse_32(self):
        """Random sparse 32x32 with density 0.2."""
        stdout, _, rc = run_binary(self.binary,
            ['--mode', 'random', '--size', '32', '--density', '0.2', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, (
            f"Value errors={info.get('VALUE_ERRORS')}, "
            f"Extra zeros={info.get('EXTRA_ZEROS')}, "
            f"Dup cols={info.get('DUP_COLS')}")

    @pytest.mark.fail_to_pass
    def test_random_sparse_64(self):
        """Random sparse 64x64 with density 0.15."""
        stdout, _, rc = run_binary(self.binary,
            ['--mode', 'random', '--size', '64', '--density', '0.15', '--seed', '99'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, (
            f"Value errors={info.get('VALUE_ERRORS')}, "
            f"Dup cols={info.get('DUP_COLS')}")

    @pytest.mark.fail_to_pass
    def test_cancellation_matrix(self):
        """Matrices with +1/-1 values that produce cancellations."""
        stdout, _, rc = run_binary(self.binary,
            ['--mode', 'cancel', '--size', '32', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('EXTRA_ZEROS') == 0, (
            f"Found {info.get('EXTRA_ZEROS')} extra zeros in output")
        assert info.get('MATCH') == 1

    @pytest.mark.fail_to_pass
    def test_no_duplicate_columns(self):
        """Output CSR should not have duplicate column indices per row."""
        stdout, _, rc = run_binary(self.binary,
            ['--mode', 'random', '--size', '48', '--density', '0.3', '--seed', '77'])
        info = parse_output(stdout)
        assert info.get('DUP_COLS') == 0, (
            f"Found {info.get('DUP_COLS')} duplicate column indices")

    @pytest.mark.fail_to_pass
    def test_nnz_matches_cpu(self):
        """Output NNZ should match CPU reference (no extra zeros)."""
        stdout, _, rc = run_binary(self.binary,
            ['--mode', 'random', '--size', '32', '--density', '0.25', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('NNZ_MATCH') == 1, (
            f"CPU NNZ={info.get('CPU_C_NNZ')}, GPU NNZ={info.get('GPU_C_NNZ')}")

    @pytest.mark.fail_to_pass
    def test_dense_pattern(self):
        """Higher density (0.5) random sparse matrix."""
        stdout, _, rc = run_binary(self.binary,
            ['--mode', 'random', '--size', '16', '--density', '0.5', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1

    # --- pass_to_pass -------------------------------------------------------

    def test_compilation_succeeds(self):
        """The source must compile without errors."""
        assert os.path.isfile(self.binary)

    def test_diagonal_matrices(self):
        """Diagonal * Diagonal should be trivially correct."""
        stdout, _, rc = run_binary(self.binary,
            ['--mode', 'diagonal', '--size', '16'])
        info = parse_output(stdout)
        assert 'MATCH' in info

    def test_output_format(self):
        """Binary should produce parseable output."""
        stdout, _, rc = run_binary(self.binary,
            ['--mode', 'random', '--size', '8', '--density', '0.3', '--seed', '1'])
        info = parse_output(stdout)
        assert 'SIZE' in info
        assert 'VALUE_ERRORS' in info
        assert 'MATCH' in info
