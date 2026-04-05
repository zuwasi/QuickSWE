#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <float.h>

#define BLOCK_SIZE 256

/* ------------------------------------------------------------------ */
/* CPU reference (DO NOT MODIFY)                                      */
/* ------------------------------------------------------------------ */
int cmp_float(const void *a, const void *b) {
    float fa = *(const float *)a, fb = *(const float *)b;
    return (fa > fb) - (fa < fb);
}

void cpu_sort(float *data, int N) {
    qsort(data, N, sizeof(float), cmp_float);
}

/* ------------------------------------------------------------------ */
/* GPU kernels                                                         */
/* ------------------------------------------------------------------ */
__global__ void pad_kernel(float *data, int N, int padded_N) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= N && i < padded_N) {
        data[i] = FLT_MAX;
    }
}

__global__ void bitonic_step_kernel(float *data, int j, int k, int padded_N) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= padded_N) return;

    int partner = i ^ (1 << j);
    if (partner <= i || partner >= padded_N) return;

    int ascending = ((i >> k) & 1) == 0;

    float ai = data[i];
    float ap = data[partner];

    if (ascending) {
        if (ai > ap) {
            data[i] = ap;
            data[partner] = ai;
        }
    } else {
        if (ai < ap) {
            data[i] = ap;
            data[partner] = ai;
        }
    }
}

/* ------------------------------------------------------------------ */
/* GPU driver                                                          */
/* ------------------------------------------------------------------ */
int next_pow2(int n) {
    int p = 1;
    while (p < n) p <<= 1;
    return p;
}

void gpu_bitonic_sort(float *h_data, int N) {
    int padded_N = next_pow2(N);
    float *d_data;

    cudaMalloc(&d_data, padded_N * sizeof(float));
    cudaMemcpy(d_data, h_data, N * sizeof(float), cudaMemcpyHostToDevice);

    /* Pad with FLT_MAX */
    if (padded_N > N) {
        int grid = (padded_N - N + BLOCK_SIZE - 1) / BLOCK_SIZE;
        pad_kernel<<<grid, BLOCK_SIZE>>>(d_data, N, padded_N);
    }

    /* Bitonic sort network */
    int log2n = 0;
    for (int tmp = padded_N; tmp > 1; tmp >>= 1) log2n++;

    for (int k = 1; k <= log2n; k++) {
        for (int j = k - 1; j >= 0; j--) {
            int grid = (padded_N + BLOCK_SIZE - 1) / BLOCK_SIZE;
            bitonic_step_kernel<<<grid, BLOCK_SIZE>>>(d_data, j, k, padded_N);
            cudaDeviceSynchronize();
        }
    }

    cudaMemcpy(h_data, d_data, N * sizeof(float), cudaMemcpyDeviceToHost);
    cudaFree(d_data);
}

/* ------------------------------------------------------------------ */
void fill_array(float *arr, int N, unsigned int seed) {
    for (int i = 0; i < N; i++) {
        seed = seed * 1103515245u + 12345u;
        arr[i] = (float)(seed % 100000) / 100.0f;
    }
}

int main(int argc, char **argv) {
    int N = 300;
    unsigned int seed = 42;

    for (int k = 1; k < argc; k++) {
        if (strcmp(argv[k], "--size") == 0 && k+1 < argc) N = atoi(argv[++k]);
        else if (strcmp(argv[k], "--seed") == 0 && k+1 < argc) seed = (unsigned int)atoi(argv[++k]);
    }

    float *cpu_data = (float *)malloc(N * sizeof(float));
    float *gpu_data = (float *)malloc(N * sizeof(float));

    fill_array(cpu_data, N, seed);
    memcpy(gpu_data, cpu_data, N * sizeof(float));

    cpu_sort(cpu_data, N);
    gpu_bitonic_sort(gpu_data, N);

    int mismatches = 0;
    int sorted = 1;
    for (int i = 0; i < N; i++) {
        if (fabsf(cpu_data[i] - gpu_data[i]) > 1e-5f) mismatches++;
        if (i > 0 && gpu_data[i] < gpu_data[i - 1] - 1e-5f) sorted = 0;
    }

    printf("N=%d\n", N);
    printf("PADDED=%d\n", next_pow2(N));
    printf("MISMATCHES=%d\n", mismatches);
    printf("SORTED=%d\n", sorted);
    printf("MATCH=%d\n", mismatches == 0 ? 1 : 0);

    free(cpu_data); free(gpu_data);
    return mismatches == 0 ? 0 : 1;
}
