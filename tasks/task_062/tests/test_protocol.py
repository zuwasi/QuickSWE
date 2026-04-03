import subprocess
import os
import tempfile
import platform
import pytest


def compile_and_run(src_files, compiler="gcc", flags=None, stdin_data=None, args=None):
    src_dir = os.path.join(os.path.dirname(__file__), '..', 'src')
    sources = [os.path.join(src_dir, f) for f in src_files]
    tmp = tempfile.mkdtemp()
    ext = '.exe' if platform.system() == 'Windows' else ''
    out = os.path.join(tmp, 'prog' + ext)
    cmd = [compiler] + sources + ['-o', out] + (flags or [])
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == 0, f"Compile failed: {r.stderr}"
    r = subprocess.run([out] + (args or []), capture_output=True, text=True, input=stdin_data, timeout=10)
    return r.stdout.strip(), r.stderr, r.returncode


SOURCES = ['protocol.c', 'main.c']


# ---------------------------------------------------------------------------
# fail_to_pass: features not yet implemented
# ---------------------------------------------------------------------------

@pytest.mark.fail_to_pass
def test_string_roundtrip():
    """Variable-length string fields should serialize and deserialize correctly."""
    stdout, _, rc = compile_and_run(SOURCES, args=['string_roundtrip'])
    assert rc == 0
    assert "sender=Alice" in stdout
    assert "payload=Hello, World!" in stdout


@pytest.mark.fail_to_pass
def test_checksum_valid():
    """Pack should include strings + checksum, making buffer > 8 bytes."""
    stdout, _, rc = compile_and_run(SOURCES, args=['checksum_valid'])
    assert rc == 0
    assert "unpack_rc=0" in stdout
    assert "msg_type=99" in stdout
    # Without string/checksum feature, packed_len is only 8 (two u32 fields).
    # With the feature, it must be larger (strings + checksum overhead).
    for line in stdout.split('\n'):
        if line.startswith("packed_len="):
            plen = int(line.split('=')[1])
            assert plen > 8, f"packed_len should be > 8 with strings+checksum, got {plen}"


@pytest.mark.fail_to_pass
def test_checksum_corrupt():
    """Corrupted buffer should fail checksum validation (unpack returns -1)."""
    stdout, _, rc = compile_and_run(SOURCES, args=['checksum_corrupt'])
    assert "unpack_rc=-1" in stdout


@pytest.mark.fail_to_pass
def test_empty_strings():
    """Empty strings should round-trip correctly."""
    stdout, _, rc = compile_and_run(SOURCES, args=['empty_strings'])
    assert rc == 0
    assert "sender_len=0" in stdout
    assert "payload_len=0" in stdout


# ---------------------------------------------------------------------------
# pass_to_pass: existing fixed-field functionality still works
# ---------------------------------------------------------------------------

def test_basic_fixed_fields():
    stdout, _, rc = compile_and_run(SOURCES, args=['basic_fixed_fields'])
    assert rc == 0
    assert "msg_type=42" in stdout
    assert "flags=65280" in stdout  # 0xFF00 = 65280
