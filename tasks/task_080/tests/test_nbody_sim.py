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
    """Parse the structured output from the nbody binary."""
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
class TestNBodySimulation:
    """Tests for CUDA N-body gravitational simulation."""

    @pytest.fixture(autouse=True)
    def _compile(self):
        self.binary = compile_cuda(['nbody_sim.cu'], 'nbody_sim')

    # --- fail_to_pass -------------------------------------------------------

    @pytest.mark.fail_to_pass
    def test_energy_conservation_256(self):
        """Energy drift should be < 1% for 256 particles, 10 steps."""
        stdout, _, rc = run_binary(self.binary,
            ['--particles', '256', '--steps', '10', '--dt', '0.001', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('PARTICLES') == 256
        assert info.get('ENERGY_OK') == 1, (
            f"GPU energy drift = {info.get('GPU_ENERGY_DRIFT')}, "
            f"CPU drift = {info.get('CPU_ENERGY_DRIFT')}")

    @pytest.mark.fail_to_pass
    def test_max_velocity_bounded(self):
        """Max velocity should stay < 20 for stable cluster."""
        stdout, _, rc = run_binary(self.binary,
            ['--particles', '256', '--steps', '10', '--dt', '0.001', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('VELOCITY_OK') == 1, (
            f"GPU max vel = {info.get('MAX_VEL_GPU')}, "
            f"CPU max vel = {info.get('MAX_VEL_CPU')}")

    @pytest.mark.fail_to_pass
    def test_position_matches_cpu(self):
        """GPU positions should be close to CPU reference."""
        stdout, _, rc = run_binary(self.binary,
            ['--particles', '256', '--steps', '10', '--dt', '0.001', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('POSITION_OK') == 1, (
            f"Avg position error = {info.get('AVG_POS_ERROR')}")

    @pytest.mark.fail_to_pass
    def test_energy_conservation_512(self):
        """Energy conservation with more particles."""
        stdout, _, rc = run_binary(self.binary,
            ['--particles', '512', '--steps', '10', '--dt', '0.001', '--seed', '99'])
        info = parse_output(stdout)
        assert info.get('ENERGY_OK') == 1, (
            f"GPU energy drift = {info.get('GPU_ENERGY_DRIFT')}")

    @pytest.mark.fail_to_pass
    def test_close_particles_no_spike(self):
        """Even with seed that creates close particles, forces shouldn't spike."""
        stdout, _, rc = run_binary(self.binary,
            ['--particles', '128', '--steps', '5', '--dt', '0.001', '--seed', '7'])
        info = parse_output(stdout)
        assert info.get('VELOCITY_OK') == 1, (
            f"Max velocity spiked to {info.get('MAX_VEL_GPU')}")
        assert info.get('ENERGY_OK') == 1

    # --- pass_to_pass -------------------------------------------------------

    def test_compilation_succeeds(self):
        """The source must compile without errors."""
        assert os.path.isfile(self.binary)

    def test_output_format(self):
        """Binary should produce parseable output."""
        stdout, _, rc = run_binary(self.binary,
            ['--particles', '32', '--steps', '1', '--dt', '0.001', '--seed', '1'])
        info = parse_output(stdout)
        assert 'PARTICLES' in info
        assert 'GPU_ENERGY_DRIFT' in info
        assert 'MAX_VEL_GPU' in info
        assert 'ENERGY_OK' in info

    def test_cpu_reference_stable(self):
        """CPU reference should have small energy drift."""
        stdout, _, rc = run_binary(self.binary,
            ['--particles', '64', '--steps', '10', '--dt', '0.001', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('CPU_ENERGY_DRIFT', 1.0) < 0.01
