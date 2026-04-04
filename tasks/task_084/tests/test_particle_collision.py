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
class TestParticleCollision:
    """Tests for CUDA spatial hash grid collision detection."""

    @pytest.fixture(autouse=True)
    def _compile(self):
        self.binary = compile_cuda(['particle_collision.cu'], 'particle_collision')

    # --- fail_to_pass -------------------------------------------------------

    @pytest.mark.fail_to_pass
    def test_collision_100_particles(self):
        """100 particles — find all collision pairs."""
        stdout, _, rc = run_binary(self.binary,
            ['--particles', '100', '--radius', '3.0', '--domain', '30.0', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, (
            f"False negatives={info.get('FALSE_NEGATIVES')}, "
            f"CPU found {info.get('CPU_COLLISIONS')}, GPU found {info.get('GPU_COLLISIONS')}")

    @pytest.mark.fail_to_pass
    def test_collision_500_particles(self):
        """500 particles — medium scale."""
        stdout, _, rc = run_binary(self.binary,
            ['--particles', '500', '--radius', '2.0', '--domain', '50.0', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('FALSE_NEGATIVES') == 0, (
            f"Missed {info.get('FALSE_NEGATIVES')} collision pairs")
        assert info.get('MATCH') == 1

    @pytest.mark.fail_to_pass
    def test_collision_1000_particles(self):
        """1000 particles — larger scale."""
        stdout, _, rc = run_binary(self.binary,
            ['--particles', '1000', '--radius', '1.5', '--domain', '50.0', '--seed', '99'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1

    @pytest.mark.fail_to_pass
    def test_collision_2000_particles(self):
        """2000 particles — stress test."""
        stdout, _, rc = run_binary(self.binary,
            ['--particles', '2000', '--radius', '1.0', '--domain', '50.0', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('FALSE_NEGATIVES') == 0
        assert info.get('DUPLICATES') == 0

    @pytest.mark.fail_to_pass
    def test_no_duplicate_pairs(self):
        """No duplicate collision pairs in output."""
        stdout, _, rc = run_binary(self.binary,
            ['--particles', '200', '--radius', '3.0', '--domain', '30.0', '--seed', '77'])
        info = parse_output(stdout)
        assert info.get('DUPLICATES') == 0, (
            f"Found {info.get('DUPLICATES')} duplicate pairs")

    @pytest.mark.fail_to_pass
    def test_boundary_wrapping(self):
        """Particles at domain boundaries should detect cross-boundary collisions."""
        stdout, _, rc = run_binary(self.binary,
            ['--particles', '200', '--radius', '2.0', '--domain', '30.0',
             '--seed', '42', '--boundary'])
        info = parse_output(stdout)
        assert info.get('FALSE_NEGATIVES') == 0, (
            f"Missed {info.get('FALSE_NEGATIVES')} pairs (likely boundary wrapping issue)")
        assert info.get('MATCH') == 1

    @pytest.mark.fail_to_pass
    def test_pair_ordering(self):
        """All pairs should be reported with i < j."""
        stdout, _, rc = run_binary(self.binary,
            ['--particles', '150', '--radius', '2.5', '--domain', '25.0', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('ORDERING_OK') == 1, "Pair ordering violated (need i < j)"

    # --- pass_to_pass -------------------------------------------------------

    def test_compilation_succeeds(self):
        """The source must compile without errors."""
        assert os.path.isfile(self.binary)

    def test_output_format(self):
        """Binary should produce parseable output."""
        stdout, _, rc = run_binary(self.binary,
            ['--particles', '50', '--radius', '5.0', '--domain', '20.0', '--seed', '1'])
        info = parse_output(stdout)
        assert 'PARTICLES' in info
        assert 'CPU_COLLISIONS' in info
        assert 'MATCH' in info

    def test_cpu_reference_works(self):
        """CPU brute-force should find some collisions."""
        stdout, _, rc = run_binary(self.binary,
            ['--particles', '100', '--radius', '5.0', '--domain', '20.0', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('CPU_COLLISIONS', 0) > 0
