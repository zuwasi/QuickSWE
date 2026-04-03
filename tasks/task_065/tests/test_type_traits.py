import subprocess
import os
import tempfile
import platform
import pytest


def compile_and_run(src_files, compiler="g++", flags=None, stdin_data=None, args=None):
    src_dir = os.path.join(os.path.dirname(__file__), '..', 'src')
    sources = [os.path.join(src_dir, f) for f in src_files]
    tmp = tempfile.mkdtemp()
    ext = '.exe' if platform.system() == 'Windows' else ''
    out = os.path.join(tmp, 'prog' + ext)
    cmd = [compiler] + sources + ['-o', out] + (flags or ['-std=c++17'])
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == 0, f"Compile failed: {r.stderr}"
    r = subprocess.run([out] + (args or []), capture_output=True, text=True, input=stdin_data, timeout=10)
    return r.stdout.strip(), r.stderr, r.returncode


def compile_mini_test(code, include_dir):
    """Compile a minimal C++ snippet that includes type_traits.h."""
    tmp = tempfile.mkdtemp()
    src = os.path.join(tmp, 'test.cpp')
    with open(src, 'w') as f:
        f.write('#include "type_traits.h"\n')
        f.write('#include <iostream>\n')
        f.write(code)
    ext = '.exe' if platform.system() == 'Windows' else ''
    out = os.path.join(tmp, 'prog' + ext)
    cmd = ['g++', src, '-I', include_dir, '-o', out, '-std=c++17']
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        return False, r.stderr, None
    r2 = subprocess.run([out], capture_output=True, text=True, timeout=10)
    return True, r2.stdout.strip(), r2.returncode


SRC_DIR = os.path.join(os.path.dirname(__file__), '..', 'src')


# ---------------------------------------------------------------------------
# fail_to_pass: these expose the missing specializations (compilation fails)
# ---------------------------------------------------------------------------

@pytest.mark.fail_to_pass
def test_is_pointer_cv_qualified():
    """my_is_pointer should handle int* const — currently fails static_assert."""
    ok, output, _ = compile_mini_test(
        'int main() {\n'
        '  static_assert(my_is_pointer<int* const>::value, "int* const is pointer");\n'
        '  static_assert(my_is_pointer<int* volatile>::value, "int* volatile is pointer");\n'
        '  static_assert(my_is_pointer<int* const volatile>::value, "int* const volatile is pointer");\n'
        '  std::cout << "is_pointer_cv=PASS" << std::endl;\n'
        '  return 0;\n'
        '}\n',
        SRC_DIR
    )
    assert ok, f"Compilation failed: {output[:500]}"
    assert "is_pointer_cv=PASS" in output


@pytest.mark.fail_to_pass
def test_remove_pointer_cv():
    """my_remove_pointer should handle int* const."""
    ok, output, _ = compile_mini_test(
        'int main() {\n'
        '  static_assert(\n'
        '    my_is_same<my_remove_pointer<int* const>::type, int>::value,\n'
        '    "remove_pointer<int* const> == int");\n'
        '  std::cout << "remove_pointer_cv=PASS" << std::endl;\n'
        '  return 0;\n'
        '}\n',
        SRC_DIR
    )
    assert ok, f"Compilation failed: {output[:500]}"
    assert "remove_pointer_cv=PASS" in output


# ---------------------------------------------------------------------------
# pass_to_pass: these work with the buggy code
# ---------------------------------------------------------------------------

def test_is_same_basic():
    ok, output, _ = compile_mini_test(
        'int main() {\n'
        '  static_assert(my_is_same<int,int>::value, "");\n'
        '  static_assert(!my_is_same<int,float>::value, "");\n'
        '  std::cout << "is_same=PASS" << std::endl;\n'
        '  return 0;\n'
        '}\n',
        SRC_DIR
    )
    assert ok, f"Compilation failed: {output[:500]}"
    assert "is_same=PASS" in output


def test_is_pointer_non_const():
    ok, output, _ = compile_mini_test(
        'int main() {\n'
        '  static_assert(my_is_pointer<int*>::value, "");\n'
        '  static_assert(!my_is_pointer<int>::value, "");\n'
        '  std::cout << "is_pointer_basic=PASS" << std::endl;\n'
        '  return 0;\n'
        '}\n',
        SRC_DIR
    )
    assert ok, f"Compilation failed: {output[:500]}"
    assert "is_pointer_basic=PASS" in output


def test_remove_const_volatile():
    """remove_const<const volatile int> correctly yields volatile int."""
    ok, output, _ = compile_mini_test(
        'int main() {\n'
        '  static_assert(\n'
        '    my_is_same<my_remove_const<const volatile int>::type, volatile int>::value,\n'
        '    "remove_const<const volatile int> == volatile int");\n'
        '  std::cout << "remove_const_volatile=PASS" << std::endl;\n'
        '  return 0;\n'
        '}\n',
        SRC_DIR
    )
    assert ok, f"Compilation failed: {output[:500]}"
    assert "remove_const_volatile=PASS" in output


def test_is_const_basic():
    ok, output, _ = compile_mini_test(
        'int main() {\n'
        '  static_assert(my_is_const<const int>::value, "");\n'
        '  static_assert(!my_is_const<int>::value, "");\n'
        '  std::cout << "is_const=PASS" << std::endl;\n'
        '  return 0;\n'
        '}\n',
        SRC_DIR
    )
    assert ok, f"Compilation failed: {output[:500]}"
    assert "is_const=PASS" in output
