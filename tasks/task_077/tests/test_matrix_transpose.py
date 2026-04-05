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
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
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
        r = subprocess.run(['nvcc', src, '-o', out],
                           capture_output=True, text=True, timeout=60)
        return r.returncode == 0
    except Exception:
        return False


def parse_output(stdout):
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


skip_no_nvcc = pytest.mark.skipif(not has_nvcc(), reason="nvcc not available")


@skip_no_nvcc
class TestMatrixTranspose:

    @pytest.fixture(autouse=True)
    def _compile(self):
        self.binary = compile_cuda(['matrix_transpose.cu'], 'matrix_transpose')

    @pytest.mark.fail_to_pass
    def test_nonsquare_64x48(self):
        stdout, _, rc = run_binary(self.binary, ['--rows', '64', '--cols', '48', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, f"MISMATCHES={info.get('MISMATCHES')}"

    @pytest.mark.fail_to_pass
    def test_nonsquare_48x64(self):
        stdout, _, rc = run_binary(self.binary, ['--rows', '48', '--cols', '64', '--seed', '99'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, f"MISMATCHES={info.get('MISMATCHES')}"

    @pytest.mark.fail_to_pass
    def test_nonsquare_100x37(self):
        stdout, _, rc = run_binary(self.binary, ['--rows', '100', '--cols', '37', '--seed', '13'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, f"MISMATCHES={info.get('MISMATCHES')}"

    @pytest.mark.fail_to_pass
    def test_square_33x33(self):
        stdout, _, rc = run_binary(self.binary, ['--rows', '33', '--cols', '33', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1, f"MISMATCHES={info.get('MISMATCHES')}"

    def test_compilation_succeeds(self):
        assert os.path.isfile(self.binary)

    def test_output_format(self):
        stdout, _, rc = run_binary(self.binary, ['--rows', '16', '--cols', '16', '--seed', '1'])
        info = parse_output(stdout)
        assert 'ROWS' in info
        assert 'MATCH' in info

    def test_square_16x16(self):
        stdout, _, rc = run_binary(self.binary, ['--rows', '16', '--cols', '16', '--seed', '42'])
        info = parse_output(stdout)
        assert info.get('MATCH') == 1
