#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define BLOCK_SIZE 256

/* ------------------------------------------------------------------ */
/* CPU reference (DO NOT MODIFY)                                      */
/* ------------------------------------------------------------------ */
int cpu_compact(const float *data, float *out, int N, float threshold) {
    int count = 0;
    for (int i = 0; i < N; i++) {
        if (data[i] > threshold) {
            out[count++] = data[i];
        }
    }
    return count;
}

/* ------------------------------------------------------------------ */
/* GPU kernels                                                         */
/* ------------------------------------------------------------------ */

/* Compute predicate flags */
__global__ void predicate_kernel(const float *data, int *flags, int N,
                                  float threshold) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < N) {
        flags[i] = (data[i] > threshold) ? 1 : 0;
    }
}

/* Inclusive prefix sum (single block, for simplicity) */
__global__ void inclusive_scan_kernel(int *flags, int *scan_out, int N) {
    extern __shared__ int temp[];
    int tid = threadIdx.x;

    temp[tid] = (tid < N) ? flags[tid] : 0;
    __syncthreads();

    for (int stride = 1; stride < blockDim.x; stride *= 2) {
        int val = 0;
        if (tid >= stride) val = temp[tid - stride];
        __syncthreads();
        temp[tid] += val;
        __syncthreads();
    }

    if (tid < N) {
        scan_out[tid] = temp[tid];
    }
}

/* Scatter selected elements using scan indices */
__global__ void scatter_kernel(const float *data, const int *flags,
                                const int *scan, float *out, int N) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < N && flags[i]) {
        int pos = scan[i];
        out[pos] = data[i];
    }
}

/* ------------------------------------------------------------------ */
/* GPU driver                                                          */
/* ------------------------------------------------------------------ */
int gpu_compact(const float *h_data, float *h_out, int N, float threshold) {
    float *d_data, *d_out;
    int *d_flags, *d_scan;

    cudaMalloc(&d_data,  N * sizeof(float));
    cudaMalloc(&d_out,   N * sizeof(float));
    cudaMalloc(&d_flags, N * sizeof(int));
    cudaMalloc(&d_scan,  N * sizeof(int));

    cudaMemcpy(d_data, h_data, N * sizeof(float), cudaMemcpyHostToDevice);
    cudaMemset(d_out, 0, N * sizeof(float));

    int grid = (N + BLOCK_SIZE - 1) / BLOCK_SIZE;

    /* Compute predicate */
    predicate_kernel<<<grid, BLOCK_SIZE>>>(d_data, d_flags, N, threshold);

    /* Inclusive scan of flags */
    inclusive_scan_kernel<<<1, N, N * sizeof(int)>>>(d_flags, d_scan, N);

    /* Scatter */
    scatter_kernel<<<grid, BLOCK_SIZE>>>(d_data, d_flags, d_scan, d_out, N);

    cudaDeviceSynchronize();

    /* Get count from last scan element */
    int count = 0;
    cudaMemcpy(&count, d_scan + N - 1, sizeof(int), cudaMemcpyDeviceToHost);

    cudaMemcpy(h_out, d_out, count * sizeof(float), cudaMemcpyDeviceToHost);

    cudaFree(d_data); cudaFree(d_out); cudaFree(d_flags); cudaFree(d_scan);
    return count;
}

/* ------------------------------------------------------------------ */
void fill_array(float *arr, int N, unsigned int seed) {
    for (int i = 0; i < N; i++) {
        seed = seed * 1103515245u + 12345u;
        arr[i] = (float)(seed % 1000) / 10.0f;
    }
}

int main(int argc, char **argv) {
    int N = 200;
    float threshold = 50.0f;
    unsigned int seed = 42;

    for (int k = 1; k < argc; k++) {
        if (strcmp(argv[k], "--size") == 0 && k+1 < argc) N = atoi(argv[++k]);
        else if (strcmp(argv[k], "--threshold") == 0 && k+1 < argc) threshold = atof(argv[++k]);
        else if (strcmp(argv[k], "--seed") == 0 && k+1 < argc) seed = (unsigned int)atoi(argv[++k]);
    }

    float *data    = (float *)malloc(N * sizeof(float));
    float *cpu_out = (float *)malloc(N * sizeof(float));
    float *gpu_out = (float *)malloc(N * sizeof(float));

    fill_array(data, N, seed);

    int cpu_count = cpu_compact(data, cpu_out, N, threshold);
    int gpu_count = gpu_compact(data, gpu_out, N, threshold);

    int count_match = (cpu_count == gpu_count) ? 1 : 0;
    int mismatches = 0;
    int cmp_len = cpu_count < gpu_count ? cpu_count : gpu_count;
    for (int i = 0; i < cmp_len; i++) {
        if (fabsf(cpu_out[i] - gpu_out[i]) > 1e-5f) mismatches++;
    }
    mismatches += abs(cpu_count - gpu_count);

    printf("N=%d\n", N);
    printf("THRESHOLD=%.1f\n", threshold);
    printf("CPU_COUNT=%d\n", cpu_count);
    printf("GPU_COUNT=%d\n", gpu_count);
    printf("COUNT_MATCH=%d\n", count_match);
    printf("MISMATCHES=%d\n", mismatches);
    printf("MATCH=%d\n", (count_match && mismatches == 0) ? 1 : 0);

    free(data); free(cpu_out); free(gpu_out);
    return (count_match && mismatches == 0) ? 0 : 1;
}
