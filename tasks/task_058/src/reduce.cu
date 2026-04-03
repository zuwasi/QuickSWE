#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#ifdef _WIN32
#include <windows.h>
#else
#include <sys/time.h>
#endif

#define BLOCK_SIZE 256

// ---------------------------------------------------------------------------
// High-resolution timer (cross-platform)
// ---------------------------------------------------------------------------
double get_time_ms(void) {
#ifdef _WIN32
    LARGE_INTEGER freq, count;
    QueryPerformanceFrequency(&freq);
    QueryPerformanceCounter(&count);
    return (double)count.QuadPart / (double)freq.QuadPart * 1000.0;
#else
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return tv.tv_sec * 1000.0 + tv.tv_usec / 1000.0;
#endif
}

// ---------------------------------------------------------------------------
// CPU reduce — correct reference implementation (DO NOT MODIFY)
// ---------------------------------------------------------------------------
float cpu_reduce_sum(const float *data, int N) {
    float sum = 0.0f;
    for (int i = 0; i < N; i++) {
        sum += data[i];
    }
    return sum;
}

// ---------------------------------------------------------------------------
// GPU reduce — STUB: not yet implemented
// ---------------------------------------------------------------------------
float gpu_reduce_sum(const float *h_data, int N) {
    // TODO: implement CUDA parallel reduction using shared memory
    // 1. Allocate device memory and copy h_data to device.
    // 2. Launch a reduction kernel that uses shared-memory tree reduction.
    // 3. Handle arbitrary N (not just powers of 2).
    // 4. Collect partial block sums and reduce them to a single value.
    // 5. Return the final sum.
    return 0.0f;
}

// ---------------------------------------------------------------------------
int main(int argc, char **argv) {
    int N = 1024;
    unsigned int seed = 42;
    int benchmark = 0;

    for (int k = 1; k < argc; k++) {
        if (strcmp(argv[k], "--size") == 0 && k + 1 < argc) {
            N = atoi(argv[++k]);
        } else if (strcmp(argv[k], "--seed") == 0 && k + 1 < argc) {
            seed = (unsigned int)atoi(argv[++k]);
        } else if (strcmp(argv[k], "--benchmark") == 0) {
            benchmark = 1;
        }
    }

    // Generate deterministic input
    float *data = (float *)malloc(N * sizeof(float));
    if (!data) { fprintf(stderr, "ERROR: malloc\n"); return 1; }

    srand(seed);
    for (int i = 0; i < N; i++) {
        data[i] = (float)(rand() % 1000) / 100.0f;  // values in [0, 10)
    }

    // CPU sum
    double t0 = get_time_ms();
    float cpu_sum = cpu_reduce_sum(data, N);
    double t1 = get_time_ms();
    double cpu_ms = t1 - t0;

    // GPU sum
    double t2 = get_time_ms();
    float gpu_sum = gpu_reduce_sum(data, N);
    double t3 = get_time_ms();
    double gpu_ms = t3 - t2;

    // Compare
    float diff = fabsf(gpu_sum - cpu_sum);
    float rel_err = (cpu_sum != 0.0f) ? diff / fabsf(cpu_sum) : diff;

    printf("SIZE=%d\n", N);
    printf("CPU_SUM=%.6f\n", cpu_sum);
    printf("GPU_SUM=%.6f\n", gpu_sum);
    printf("ABS_DIFF=%.6f\n", diff);
    printf("REL_ERR=%.8f\n", rel_err);

    if (benchmark) {
        printf("CPU_TIME_MS=%.4f\n", cpu_ms);
        printf("GPU_TIME_MS=%.4f\n", gpu_ms);
    }

    int ok = (rel_err < 1e-4f) ? 1 : 0;
    printf("MATCH=%d\n", ok);

    free(data);
    return ok ? 0 : 1;
}
