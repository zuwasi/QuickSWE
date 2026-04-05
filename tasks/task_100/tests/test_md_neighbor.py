import subprocess, os, tempfile, platform, shutil, re
import pytest

def compile_cuda(src_files, output_name, extra_flags=None):
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
    cmd = [path] + (args or [])
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return result.stdout, result.stderr, result.returncode

def has_nvcc():
    if shutil.which('nvcc') is None:
        return False
    try:
        tmp = tempfile.mkdtemp()
        src = os.path.join(tmp, 'test.cu')
        with open(src, 'w') as f:
            f.write('int main(){return 0;}\n')
        ext = '.exe' if platform.system() == 'Windows' else ''
        out = os.path.join(tmp, 'test' + ext)
        r = subprocess.run(['nvcc', src, '-o', out], capture_output=True, text=True, timeout=60)
        return r.returncode == 0
    except Exception:
        return False

def parse_output(stdout):
    info = {}
    for line in stdout.splitlines():
        m = re.match(r'^([A-Z_]+)=([\d.eE+\-]+)$', line)
        if m:
            key, val = m.group(1), m.group(2)
            info[key] = float(val) if ('.' in val or 'e' in val.lower()) else int(val)
    return info

skip_no_nvcc = pytest.mark.skipif(not has_nvcc(), reason="nvcc not available")

@skip_no_nvcc
class TestMDNeighbor:
    @pytest.fixture(autouse=True)
    def _compile(self):
        self.binary = compile_cuda(['md_neighbor.cu'], 'md_neighbor')

    @pytest.mark.fail_to_pass
    def test_64_atoms(self):
        stdout, _, rc = run_binary(self.binary, ['--size', '64', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, f"MISMATCHES={info.get('MISMATCHES')}"

    @pytest.mark.fail_to_pass
    def test_128_atoms(self):
        stdout, _, rc = run_binary(self.binary, ['--size', '128', '--seed', '99'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1

    @pytest.mark.fail_to_pass
    def test_no_nans(self):
        stdout, _, rc = run_binary(self.binary, ['--size', '64', '--seed', '13'])
        info = parse_output(stdout)
        assert info.get('NAN_COUNT', 999) == 0

    @pytest.mark.fail_to_pass
    def test_momentum_conservation(self):
        stdout, _, rc = run_binary(self.binary, ['--size', '32', '--seed', '777'])
        info = parse_output(stdout)
        assert info.get('GPU_MOMENTUM', 999.0) < 1.0

    @pytest.mark.fail_to_pass
    def test_different_cutoff(self):
        stdout, _, rc = run_binary(self.binary, ['--size', '64', '--cutoff', '4.0', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1

    @pytest.mark.fail_to_pass
    def test_256_atoms(self):
        stdout, _, rc = run_binary(self.binary, ['--size', '256', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1

    @pytest.mark.fail_to_pass
    def test_small(self):
        stdout, _, rc = run_binary(self.binary, ['--size', '16', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1

    def test_compilation_succeeds(self):
        assert os.path.isfile(self.binary)

    def test_output_format(self):
        stdout, _, rc = run_binary(self.binary, ['--size', '8', '--seed', '1'])
        info = parse_output(stdout)
        assert 'N' in info and 'MATCH' in info
