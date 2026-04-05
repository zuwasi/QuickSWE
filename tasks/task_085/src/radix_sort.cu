#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define BLOCK_SIZE 256
#define BITS_PER_PASS 1

/* ------------------------------------------------------------------ */
/* CPU reference (DO NOT MODIFY)                                      */
/* ------------------------------------------------------------------ */
int cmp_int(const void *a, const void *b) {
    int ia = *(const int *)a, ib = *(const int *)b;
    return (ia > ib) - (ia < ib);
}

void cpu_sort(int *data, int N) {
    qsort(data, N, sizeof(int), cmp_int);
}

/* ------------------------------------------------------------------ */
/* GPU kernels                                                         */
/* ------------------------------------------------------------------ */

/* Count 0s and 1s for current bit position */
__global__ void count_kernel(const int *data, int *count0, int *count1,
                              int N, int bit) {
    __shared__ int s_c0, s_c1;
    if (threadIdx.x == 0) { s_c0 = 0; s_c1 = 0; }
    __syncthreads();

    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < N) {
        unsigned int val = (unsigned int)data[i];
        int b = (val >> bit) & 1;
        if (b == 0)
            atomicAdd(&s_c0, 1);
        else
            atomicAdd(&s_c1, 1);
    }
    __syncthreads();

    if (threadIdx.x == 0) {
        atomicAdd(count0, s_c0);
        atomicAdd(count1, s_c1);
    }
}

/* Scatter elements based on bit value */
__global__ void scatter_kernel(const int *in, int *out, int N,
                                int bit, int num_zeros) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= N) return;

    unsigned int val = (unsigned int)in[i];
    int b = (val >> bit) & 1;

    /* Compute position: count how many elements before me have same bit */
    int pos = 0;
    for (int j = 0; j < i; j++) {
        unsigned int vj = (unsigned int)in[j];
        int bj = (vj >> bit) & 1;
        if (bj == b) pos++;
    }

    if (b == 0) {
        out[pos] = in[i];
    } else {
        out[num_zeros + pos] = in[i];
    }
}

/* ------------------------------------------------------------------ */
/* GPU driver                                                          */
/* ------------------------------------------------------------------ */
void gpu_radix_sort(int *h_data, int N) {
    int *d_buf0, *d_buf1;
    int *d_count0, *d_count1;

    cudaMalloc(&d_buf0, N * sizeof(int));
    cudaMalloc(&d_buf1, N * sizeof(int));
    cudaMalloc(&d_count0, sizeof(int));
    cudaMalloc(&d_count1, sizeof(int));

    cudaMemcpy(d_buf0, h_data, N * sizeof(int), cudaMemcpyHostToDevice);

    int grid = (N + BLOCK_SIZE - 1) / BLOCK_SIZE;

    for (int bit = 0; bit < 32; bit++) {
        cudaMemset(d_count0, 0, sizeof(int));
        cudaMemset(d_count1, 0, sizeof(int));

        count_kernel<<<grid, BLOCK_SIZE>>>(d_buf0, d_count0, d_count1, N, bit);
        cudaDeviceSynchronize();

        int h_c0 = 0;
        cudaMemcpy(&h_c0, d_count0, sizeof(int), cudaMemcpyDeviceToHost);

        scatter_kernel<<<grid, BLOCK_SIZE>>>(d_buf0, d_buf1, N, bit, h_c0);
        cudaDeviceSynchronize();

        /* Swap buffers */
        int *tmp = d_buf0;
        d_buf0 = d_buf1;
        d_buf1 = tmp;
    }

    cudaMemcpy(h_data, d_buf0, N * sizeof(int), cudaMemcpyDeviceToHost);

    cudaFree(d_buf0); cudaFree(d_buf1);
    cudaFree(d_count0); cudaFree(d_count1);
}

/* ------------------------------------------------------------------ */
void fill_array(int *arr, int N, unsigned int seed) {
    for (int i = 0; i < N; i++) {
        seed = seed * 1103515245u + 12345u;
        arr[i] = (int)(seed % 2000) - 1000;  /* range -1000..999 */
    }
}

int main(int argc, char **argv) {
    int N = 200;
    unsigned int seed = 42;
    int mode = 0;  /* 0=mixed, 1=positive-only */

    for (int k = 1; k < argc; k++) {
        if (strcmp(argv[k], "--size") == 0 && k+1 < argc) N = atoi(argv[++k]);
        else if (strcmp(argv[k], "--seed") == 0 && k+1 < argc) seed = (unsigned int)atoi(argv[++k]);
        else if (strcmp(argv[k], "--mode") == 0 && k+1 < argc) mode = atoi(argv[++k]);
    }

    int *cpu_data = (int *)malloc(N * sizeof(int));
    int *gpu_data = (int *)malloc(N * sizeof(int));

    fill_array(cpu_data, N, seed);
    if (mode == 1) {
        for (int i = 0; i < N; i++) cpu_data[i] = abs(cpu_data[i]);
    }
    memcpy(gpu_data, cpu_data, N * sizeof(int));

    cpu_sort(cpu_data, N);
    gpu_radix_sort(gpu_data, N);

    int mismatches = 0;
    int sorted = 1;
    int neg_after_pos = 0;
    for (int i = 0; i < N; i++) {
        if (cpu_data[i] != gpu_data[i]) mismatches++;
        if (i > 0 && gpu_data[i] < gpu_data[i - 1]) sorted = 0;
        if (i > 0 && gpu_data[i] < 0 && gpu_data[i - 1] >= 0) neg_after_pos = 1;
    }

    printf("N=%d\n", N);
    printf("MODE=%d\n", mode);
    printf("MISMATCHES=%d\n", mismatches);
    printf("SORTED=%d\n", sorted);
    printf("NEG_AFTER_POS=%d\n", neg_after_pos);
    printf("MATCH=%d\n", mismatches == 0 ? 1 : 0);

    free(cpu_data); free(gpu_data);
    return mismatches == 0 ? 0 : 1;
}
