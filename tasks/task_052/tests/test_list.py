import subprocess
import os
import sys
import tempfile
import platform
import pytest


def compile_c(src_files, output_name, extra_flags=None):
    """Compile C files with gcc, return path to executable."""
    src_dir = os.path.join(os.path.dirname(__file__), '..', 'src')
    sources = [os.path.join(src_dir, f) for f in src_files]
    tmp = tempfile.mkdtemp()
    ext = '.exe' if platform.system() == 'Windows' else ''
    out_path = os.path.join(tmp, output_name + ext)
    cmd = ['gcc'] + sources + ['-o', out_path, '-lm']
    if extra_flags:
        cmd.extend(extra_flags)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed:\n{result.stderr}")
    return out_path


def run_binary(path, stdin_data=None, args=None):
    """Run compiled binary and return (stdout, stderr, returncode)."""
    cmd = [path] + (args or [])
    result = subprocess.run(cmd, capture_output=True, text=True,
                            input=stdin_data, timeout=10)
    return result.stdout, result.stderr, result.returncode


def compile_with_tracking(output_name):
    """Compile the list code with our malloc/free tracking wrapper."""
    src_dir = os.path.join(os.path.dirname(__file__), '..', 'src')
    # We compile a special version that wraps malloc/free
    tracking_src = os.path.join(tempfile.mkdtemp(), 'track_main.c')

    tracking_code = r"""
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Tracking counters */
static int alloc_count = 0;
static int free_count = 0;
static void *alloc_ptrs[10000];
static int alloc_idx = 0;

void *tracked_malloc(size_t size) {
    void *p = malloc(size);
    if (p) {
        alloc_count++;
        if (alloc_idx < 10000) alloc_ptrs[alloc_idx++] = p;
    }
    return p;
}

void tracked_free(void *p) {
    if (p) {
        free_count++;
        free(p);
    }
}

char *tracked_strdup(const char *s) {
    size_t len = strlen(s) + 1;
    char *dup = (char *)tracked_malloc(len);
    if (dup) memcpy(dup, s, len);
    return dup;
}

/* Override malloc/free/_strdup via macros BEFORE including list code */
#define malloc tracked_malloc
#define free tracked_free
#define _strdup tracked_strdup
#define strdup tracked_strdup

/* Now include list.c directly so macros apply */
""" + f'#include "{os.path.join(src_dir, "list.c").replace(chr(92), "/")}"\n' + r"""

#undef malloc
#undef free
#undef _strdup
#undef strdup

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Usage: %s <test>\n", argv[0]);
        return 1;
    }

    if (strcmp(argv[1], "delete_leak") == 0) {
        alloc_count = 0;
        free_count = 0;

        List *list = list_create();
        list_insert(list, "alpha");
        list_insert(list, "bravo");
        list_insert(list, "charlie");

        /* Delete one item - should free both node and data */
        list_delete(list, "bravo");

        /* Destroy rest */
        list_destroy(list);

        printf("ALLOCS: %d\n", alloc_count);
        printf("FREES: %d\n", free_count);
        if (alloc_count == free_count) {
            printf("RESULT: NO_LEAK\n");
        } else {
            printf("RESULT: LEAK (%d unfreed)\n", alloc_count - free_count);
        }

    } else if (strcmp(argv[1], "destroy_leak") == 0) {
        alloc_count = 0;
        free_count = 0;

        List *list = list_create();
        list_insert(list, "x");
        list_insert(list, "y");

        /* Just destroy without deleting - should free everything */
        list_destroy(list);

        printf("ALLOCS: %d\n", alloc_count);
        printf("FREES: %d\n", free_count);
        if (alloc_count == free_count) {
            printf("RESULT: NO_LEAK\n");
        } else {
            printf("RESULT: LEAK (%d unfreed)\n", alloc_count - free_count);
        }

    } else if (strcmp(argv[1], "full_cycle") == 0) {
        alloc_count = 0;
        free_count = 0;

        List *list = list_create();
        const char *items[] = {"one", "two", "three", "four", "five"};
        for (int i = 0; i < 5; i++) {
            list_insert(list, items[i]);
        }

        /* Delete some */
        list_delete(list, "two");
        list_delete(list, "four");

        /* Destroy the rest */
        list_destroy(list);

        printf("ALLOCS: %d\n", alloc_count);
        printf("FREES: %d\n", free_count);
        if (alloc_count == free_count) {
            printf("RESULT: NO_LEAK\n");
        } else {
            printf("RESULT: LEAK (%d unfreed)\n", alloc_count - free_count);
        }

    } else if (strcmp(argv[1], "basic") == 0) {
        List *list = list_create();
        list_insert(list, "hello");
        list_insert(list, "world");
        ListNode *n = list_find(list, "hello");
        if (n && strcmp(n->data, "hello") == 0) {
            printf("FIND: OK\n");
        } else {
            printf("FIND: FAIL\n");
        }
        printf("LENGTH: %zu\n", list->length);
        list_destroy(list);
        printf("PASS: basic\n");

    } else {
        printf("Unknown: %s\n", argv[1]);
        return 1;
    }
    return 0;
}
"""

    with open(tracking_src, 'w') as f:
        f.write(tracking_code)

    tmp = tempfile.mkdtemp()
    ext = '.exe' if platform.system() == 'Windows' else ''
    out_path = os.path.join(tmp, output_name + ext)

    cmd = ['gcc', tracking_src, '-o', out_path, '-lm',
           '-I', src_dir]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed:\n{result.stderr}")
    return out_path


@pytest.fixture(scope="module")
def list_binary():
    """Compile the list program with tracking for the module."""
    return compile_with_tracking('list_track_test')


@pytest.fixture(scope="module")
def list_basic_binary():
    """Compile the basic list program."""
    return compile_c(['list.c', 'main.c'], 'list_basic_test')


# ---- pass_to_pass ----

class TestPassToPass:

    def test_compilation_succeeds(self):
        """The code should compile."""
        binary = compile_c(['list.c', 'main.c'], 'list_compile_check')
        assert os.path.exists(binary)

    def test_basic_operations(self, list_basic_binary):
        """Basic insert, find, delete produce correct output."""
        stdout, stderr, rc = run_binary(list_basic_binary, args=['basic_ops'])
        assert rc == 0
        assert "PASS: basic_ops" in stdout
        assert "LIST: alpha bravo charlie" in stdout
        assert "FOUND: bravo" in stdout
        assert "BRAVO_AFTER_DELETE: gone" in stdout


# ---- fail_to_pass ----

class TestFailToPass:

    @pytest.mark.fail_to_pass
    def test_delete_frees_data(self, list_binary):
        """list_delete should free node's strdup'd data. Bug: it doesn't."""
        stdout, stderr, rc = run_binary(list_binary, args=['delete_leak'])
        assert rc == 0, f"Crashed: {stderr}"
        assert "RESULT: NO_LEAK" in stdout, f"Memory leak detected after delete: {stdout}"

    @pytest.mark.fail_to_pass
    def test_destroy_frees_list_struct(self, list_binary):
        """list_destroy should free the list struct. Bug: it doesn't."""
        stdout, stderr, rc = run_binary(list_binary, args=['destroy_leak'])
        assert rc == 0, f"Crashed: {stderr}"
        assert "RESULT: NO_LEAK" in stdout, f"Memory leak detected after destroy: {stdout}"

    @pytest.mark.fail_to_pass
    def test_full_cycle_no_leaks(self, list_binary):
        """Full insert/delete/destroy cycle should have zero leaks."""
        stdout, stderr, rc = run_binary(list_binary, args=['full_cycle'])
        assert rc == 0, f"Crashed: {stderr}"
        assert "RESULT: NO_LEAK" in stdout, f"Leaks in full cycle: {stdout}"
