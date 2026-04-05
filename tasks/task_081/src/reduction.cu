#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define BLOCK_SIZE 256
#define WARP_SIZE 32

/* ------------------------------------------------------------------ */
/* CPU reference (DO NOT MODIFY)                                      */
/* ------------------------------------------------------------------ */
double cpu_reduce(const float *data, int N) {
    double sum = 0.0;
    for (int i = 0; i < N; i++) sum += (double)data[i];
    return sum;
}

/* ------------------------------------------------------------------ */
/* Warp-level reduction using shuffle — has incorrect mask             */
/* ------------------------------------------------------------------ */
__device__ float warp_reduce_sum(float val) {
    unsigned mask = 0x0000FFFF;
    for (int offset = WARP_SIZE / 2; offset > 0; offset /= 2) {
        val += __shfl_down_sync(mask, val, offset);
    }
    return val;
}

/* ------------------------------------------------------------------ */
/* GPU kernel                                                          */
/* ------------------------------------------------------------------ */
__global__ void reduce_kernel(const float *data, float *partial_sums,
                               int N) {
    __shared__ float sdata[BLOCK_SIZE];

    int tid = threadIdx.x;
    int gid = blockIdx.x * blockDim.x * 2 + threadIdx.x;

    float sum = 0.0f;
    if (gid < N) sum = data[gid];
    if (gid + blockDim.x < N) sum += data[gid + blockDim.x];
    sdata[tid] = sum;
    __syncthreads();

    /* Shared memory reduction down to warp size */
    for (int s = blockDim.x / 2; s > WARP_SIZE; s >>= 1) {
        if (tid < s) {
            sdata[tid] += sdata[tid + s];
        }
        __syncthreads();
    }

    /* Final warp reduction using shuffle */
    if (tid < WARP_SIZE) {
        sum = sdata[tid];
        sum = warp_reduce_sum(sum);
    }

    if (tid == 0) {
        partial_sums[blockIdx.x] = sum;
    }
}

/* ------------------------------------------------------------------ */
/* GPU driver                                                          */
/* ------------------------------------------------------------------ */
double gpu_reduce(const float *h_data, int N) {
    float *d_data;
    cudaMalloc(&d_data, N * sizeof(float));
    cudaMemcpy(d_data, h_data, N * sizeof(float), cudaMemcpyHostToDevice);

    int num_blocks = (N + BLOCK_SIZE * 2 - 1) / (BLOCK_SIZE * 2);
    float *d_partial;
    cudaMalloc(&d_partial, num_blocks * sizeof(float));

    reduce_kernel<<<num_blocks, BLOCK_SIZE>>>(d_data, d_partial, N);
    cudaDeviceSynchronize();

    /* Copy partial sums back and reduce on CPU */
    float *h_partial = (float *)malloc(num_blocks * sizeof(float));
    cudaMemcpy(h_partial, d_partial, num_blocks * sizeof(float),
               cudaMemcpyDeviceToHost);

    double total = 0.0;
    for (int i = 0; i < num_blocks; i++) total += (double)h_partial[i];

    cudaFree(d_data);
    cudaFree(d_partial);
    free(h_partial);
    return total;
}

/* ------------------------------------------------------------------ */
void fill_array(float *arr, int N, unsigned int seed) {
    for (int i = 0; i < N; i++) {
        seed = seed * 1103515245u + 12345u;
        arr[i] = (float)(seed % 1000) / 100.0f;
    }
}

int main(int argc, char **argv) {
    int N = 10000;
    unsigned int seed = 42;

    for (int k = 1; k < argc; k++) {
        if (strcmp(argv[k], "--size") == 0 && k+1 < argc) N = atoi(argv[++k]);
        else if (strcmp(argv[k], "--seed") == 0 && k+1 < argc) seed = (unsigned int)atoi(argv[++k]);
    }

    float *data = (float *)malloc(N * sizeof(float));
    fill_array(data, N, seed);

    double cpu_sum = cpu_reduce(data, N);
    double gpu_sum = gpu_reduce(data, N);

    double rel_err = fabs(cpu_sum - gpu_sum) / fabs(cpu_sum + 1e-12);

    printf("N=%d\n", N);
    printf("CPU_SUM=%.6f\n", cpu_sum);
    printf("GPU_SUM=%.6f\n", gpu_sum);
    printf("REL_ERROR=%.6e\n", rel_err);
    printf("MATCH=%d\n", rel_err < 1e-3 ? 1 : 0);

    free(data);
    return rel_err < 1e-3 ? 0 : 1;
}
