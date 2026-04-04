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
class TestRadixSort:
    """Tests for CUDA radix sort."""

    @pytest.fixture(autouse=True)
    def _compile(self):
        self.binary = compile_cuda(['radix_sort.cu'], 'radix_sort')

    # --- fail_to_pass -------------------------------------------------------

    @pytest.mark.fail_to_pass
    def test_sort_n_1024(self):
        """N=1024: medium array — scatter offset bug causes corruption."""
        stdout, _, rc = run_binary(self.binary, ['--size', '1024', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('SIZE') == 1024
        assert info.get('SORTED') == 1, "Output is not sorted"
        assert info.get('MATCH') == 1, (
            f"MISMATCHES={info.get('MISMATCHES')}, "
            f"LOST={info.get('LOST')}, DUPED={info.get('DUPED')}")

    @pytest.mark.fail_to_pass
    def test_sort_n_100(self):
        """N=100: small array."""
        stdout, _, rc = run_binary(self.binary, ['--size', '100', '--seed', '7'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, (
            f"MISMATCHES={info.get('MISMATCHES')}, "
            f"LOST={info.get('LOST')}, DUPED={info.get('DUPED')}")

    @pytest.mark.fail_to_pass
    def test_no_lost_elements(self):
        """N=500: no elements should be lost."""
        stdout, _, rc = run_binary(self.binary, ['--size', '500', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('LOST', -1) == 0, (
            f"Lost {info.get('LOST')} elements")

    @pytest.mark.fail_to_pass
    def test_no_duplicated_elements(self):
        """N=500: no elements should be duplicated."""
        stdout, _, rc = run_binary(self.binary, ['--size', '500', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('DUPED', -1) == 0, (
            f"Duplicated {info.get('DUPED')} elements")

    @pytest.mark.fail_to_pass
    def test_sort_n_4096(self):
        """N=4096: larger array stresses multi-block scatter."""
        stdout, _, rc = run_binary(self.binary, ['--size', '4096', '--seed', '99'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, (
            f"MISMATCHES={info.get('MISMATCHES')}")

    @pytest.mark.fail_to_pass
    def test_sort_n_33(self):
        """N=33: very small, partial block."""
        stdout, _, rc = run_binary(self.binary, ['--size', '33', '--seed', '1'])
        info = parse_output(stdout)
        assert info.get('SORTED') == 1, "Output is not sorted"
        assert info.get('MATCH') == 1

    # --- pass_to_pass -------------------------------------------------------

    def test_compilation_succeeds(self):
        """Source must compile without errors."""
        assert os.path.isfile(self.binary)

    def test_output_format(self):
        """Binary should produce parseable output."""
        stdout, _, rc = run_binary(self.binary, ['--size', '16', '--seed', '1'])
        info = parse_output(stdout)
        assert 'SIZE' in info
        assert 'MISMATCHES' in info
        assert 'SORTED' in info
        assert 'LOST' in info
        assert 'DUPED' in info
        assert 'MATCH' in info
