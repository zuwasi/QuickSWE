#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <float.h>

#define BLOCK_SIZE 256

// ---------------------------------------------------------------------------
// CPU reference sort (DO NOT MODIFY)
// ---------------------------------------------------------------------------
static int cmp_float_asc(const void *a, const void *b) {
    float fa = *(const float *)a;
    float fb = *(const float *)b;
    if (fa < fb) return -1;
    if (fa > fb) return  1;
    return 0;
}

void cpu_sort(const float *in, float *out, int N) {
    memcpy(out, in, N * sizeof(float));
    qsort(out, N, sizeof(float), cmp_float_asc);
}

// ---------------------------------------------------------------------------
// CUDA bitonic sort — STUB (to be implemented)
// ---------------------------------------------------------------------------

// TODO: implement bitonic sort kernel(s)
// __global__ void bitonic_step_kernel(float *data, int j, int k, int N) { ... }

void gpu_bitonic_sort(const float *h_in, float *h_out, int N) {
    // TODO: implement bitonic sort
    // 1. Compute padded_N = next power of 2 >= N.
    // 2. Allocate device array of padded_N floats.
    // 3. Copy h_in to device, fill remaining with FLT_MAX.
    // 4. Run bitonic sort network (stages and steps).
    // 5. Copy first N elements back to h_out.
    memcpy(h_out, h_in, N * sizeof(float));
}

// ---------------------------------------------------------------------------
int main(int argc, char **argv) {
    int N = 1024;
    unsigned int seed = 42;

    for (int k = 1; k < argc; k++) {
        if (strcmp(argv[k], "--size") == 0 && k + 1 < argc) {
            N = atoi(argv[++k]);
        } else if (strcmp(argv[k], "--seed") == 0 && k + 1 < argc) {
            seed = (unsigned int)atoi(argv[++k]);
        }
    }

    float *in      = (float *)malloc(N * sizeof(float));
    float *cpu_out = (float *)malloc(N * sizeof(float));
    float *gpu_out = (float *)malloc(N * sizeof(float));
    if (!in || !cpu_out || !gpu_out) {
        fprintf(stderr, "ERROR: malloc\n");
        return 1;
    }

    srand(seed);
    for (int i = 0; i < N; i++) {
        in[i] = (float)(rand() % 100000) / 100.0f;
    }

    cpu_sort(in, cpu_out, N);
    gpu_bitonic_sort(in, gpu_out, N);

    int mismatches = 0;
    int first_bad = -1;
    for (int i = 0; i < N; i++) {
        if (cpu_out[i] != gpu_out[i]) {
            if (first_bad < 0) first_bad = i;
            mismatches++;
        }
    }

    // Check that output is actually sorted
    int sorted = 1;
    for (int i = 1; i < N; i++) {
        if (gpu_out[i] < gpu_out[i - 1]) {
            sorted = 0;
            break;
        }
    }

    printf("SIZE=%d\n", N);
    printf("MISMATCHES=%d\n", mismatches);
    printf("SORTED=%d\n", sorted);
    if (first_bad >= 0) {
        printf("FIRST_BAD_INDEX=%d\n", first_bad);
        printf("EXPECTED=%.2f\n", cpu_out[first_bad]);
        printf("GOT=%.2f\n", gpu_out[first_bad]);
    }
    printf("MATCH=%d\n", (mismatches == 0 && sorted) ? 1 : 0);

    free(in);
    free(cpu_out);
    free(gpu_out);
    return (mismatches == 0 && sorted) ? 0 : 1;
}
