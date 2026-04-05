#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define NUM_BINS 256
#define BLOCK_SIZE 256

/* ------------------------------------------------------------------ */
/* CPU reference (DO NOT MODIFY)                                      */
/* ------------------------------------------------------------------ */
void cpu_histogram(const unsigned char *data, int *hist, int N) {
    memset(hist, 0, NUM_BINS * sizeof(int));
    for (int i = 0; i < N; i++) {
        hist[data[i]]++;
    }
}

/* ------------------------------------------------------------------ */
/* GPU kernel                                                          */
/* ------------------------------------------------------------------ */
__global__ void histogram_kernel(const unsigned char *data, int *hist, int N) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < N) {
        int bin = data[i];
        hist[bin] += 1;
    }
}

/* ------------------------------------------------------------------ */
/* GPU driver                                                          */
/* ------------------------------------------------------------------ */
void gpu_histogram(const unsigned char *h_data, int *h_hist, int N) {
    unsigned char *d_data;
    int *d_hist;

    cudaMalloc(&d_data, N * sizeof(unsigned char));
    cudaMalloc(&d_hist, NUM_BINS * sizeof(int));

    cudaMemcpy(d_data, h_data, N * sizeof(unsigned char), cudaMemcpyHostToDevice);
    cudaMemset(d_hist, 0, NUM_BINS * sizeof(int));

    int grid = (N + BLOCK_SIZE - 1) / BLOCK_SIZE;
    histogram_kernel<<<grid, BLOCK_SIZE>>>(d_data, d_hist, N);
    cudaDeviceSynchronize();

    cudaMemcpy(h_hist, d_hist, NUM_BINS * sizeof(int), cudaMemcpyDeviceToHost);

    cudaFree(d_data);
    cudaFree(d_hist);
}

/* ------------------------------------------------------------------ */
void fill_data(unsigned char *arr, int N, unsigned int seed) {
    for (int i = 0; i < N; i++) {
        seed = seed * 1103515245u + 12345u;
        arr[i] = (unsigned char)(seed >> 16);
    }
}

int main(int argc, char **argv) {
    int N = 10000;
    unsigned int seed = 42;

    for (int k = 1; k < argc; k++) {
        if (strcmp(argv[k], "--size") == 0 && k+1 < argc) N = atoi(argv[++k]);
        else if (strcmp(argv[k], "--seed") == 0 && k+1 < argc) seed = (unsigned int)atoi(argv[++k]);
    }

    unsigned char *data = (unsigned char *)malloc(N);
    int *cpu_hist = (int *)calloc(NUM_BINS, sizeof(int));
    int *gpu_hist = (int *)calloc(NUM_BINS, sizeof(int));

    fill_data(data, N, seed);
    cpu_histogram(data, cpu_hist, N);
    gpu_histogram(data, gpu_hist, N);

    int mismatches = 0;
    int max_diff = 0;
    int cpu_total = 0, gpu_total = 0;
    for (int i = 0; i < NUM_BINS; i++) {
        cpu_total += cpu_hist[i];
        gpu_total += gpu_hist[i];
        int diff = abs(cpu_hist[i] - gpu_hist[i]);
        if (diff > max_diff) max_diff = diff;
        if (diff > 0) mismatches++;
    }

    printf("N=%d\n", N);
    printf("BINS=%d\n", NUM_BINS);
    printf("MISMATCHES=%d\n", mismatches);
    printf("MAX_DIFF=%d\n", max_diff);
    printf("CPU_TOTAL=%d\n", cpu_total);
    printf("GPU_TOTAL=%d\n", gpu_total);
    printf("MATCH=%d\n", mismatches == 0 ? 1 : 0);

    free(data); free(cpu_hist); free(gpu_hist);
    return mismatches == 0 ? 0 : 1;
}
