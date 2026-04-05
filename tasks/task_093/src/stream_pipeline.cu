#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define BLOCK_SIZE 256

/* ------------------------------------------------------------------ */
/* CPU reference pipeline (DO NOT MODIFY)                             */
/* ------------------------------------------------------------------ */
void cpu_pipeline(const float *in, float *out, float *sum_out,
                  int N) {
    /* Stage 1: transform x -> x^2 + 1 */
    float *transformed = (float *)malloc(N * sizeof(float));
    for (int i = 0; i < N; i++) {
        transformed[i] = in[i] * in[i] + 1.0f;
    }

    /* Stage 2: compute sum */
    double total = 0.0;
    for (int i = 0; i < N; i++) total += (double)transformed[i];
    *sum_out = (float)total;

    /* Stage 3: normalize */
    for (int i = 0; i < N; i++) {
        out[i] = transformed[i] / (float)total;
    }

    free(transformed);
}

/* ------------------------------------------------------------------ */
/* GPU kernels                                                         */
/* ------------------------------------------------------------------ */
__global__ void transform_kernel(const float *in, float *out, int N) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < N) out[i] = in[i] * in[i] + 1.0f;
}

__global__ void reduce_kernel(const float *data, float *result, int N) {
    __shared__ float sdata[BLOCK_SIZE];
    int tid = threadIdx.x;
    int gid = blockIdx.x * blockDim.x + threadIdx.x;

    sdata[tid] = (gid < N) ? data[gid] : 0.0f;
    __syncthreads();

    for (int s = blockDim.x / 2; s > 0; s >>= 1) {
        if (tid < s) sdata[tid] += sdata[tid + s];
        __syncthreads();
    }

    if (tid == 0) atomicAdd(result, sdata[0]);
}

__global__ void normalize_kernel(const float *in, float *out,
                                  const float *total, int N) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < N) out[i] = in[i] / *total;
}

/* ------------------------------------------------------------------ */
/* GPU multi-stream pipeline                                           */
/* ------------------------------------------------------------------ */
void gpu_pipeline(const float *h_in, float *h_out, float *h_sum, int N) {
    float *d_in, *d_transformed, *d_out, *d_sum;

    cudaMalloc(&d_in,          N * sizeof(float));
    cudaMalloc(&d_transformed, N * sizeof(float));
    cudaMalloc(&d_out,         N * sizeof(float));
    cudaMalloc(&d_sum,         sizeof(float));

    cudaMemcpy(d_in, h_in, N * sizeof(float), cudaMemcpyHostToDevice);
    cudaMemset(d_sum, 0, sizeof(float));

    cudaStream_t s1, s2, s3;
    cudaStreamCreate(&s1);
    cudaStreamCreate(&s2);
    cudaStreamCreate(&s3);

    cudaEvent_t e_transform_done, e_reduce_done;
    cudaEventCreate(&e_transform_done);
    cudaEventCreate(&e_reduce_done);

    int grid = (N + BLOCK_SIZE - 1) / BLOCK_SIZE;

    /* Stage 1: transform on stream s1 */
    transform_kernel<<<grid, BLOCK_SIZE, 0, s1>>>(d_in, d_transformed, N);

    /* Record event — records on default stream instead of s1 */
    cudaEventRecord(e_transform_done, 0);

    /* Stage 2 should wait for stage 1, but waits on wrong stream */
    cudaStreamWaitEvent(s1, e_transform_done, 0);
    reduce_kernel<<<grid, BLOCK_SIZE, 0, s2>>>(d_transformed, d_sum, N);

    /* Record event — records on default stream instead of s2 */
    cudaEventRecord(e_reduce_done, 0);

    /* Stage 3 should wait for stage 2, but waits on wrong stream */
    cudaStreamWaitEvent(s2, e_reduce_done, 0);
    normalize_kernel<<<grid, BLOCK_SIZE, 0, s3>>>(d_transformed, d_out, d_sum, N);

    cudaDeviceSynchronize();

    cudaMemcpy(h_out, d_out, N * sizeof(float), cudaMemcpyDeviceToHost);
    cudaMemcpy(h_sum, d_sum, sizeof(float), cudaMemcpyDeviceToHost);

    cudaEventDestroy(e_transform_done);
    cudaEventDestroy(e_reduce_done);
    cudaStreamDestroy(s1); cudaStreamDestroy(s2); cudaStreamDestroy(s3);
    cudaFree(d_in); cudaFree(d_transformed); cudaFree(d_out); cudaFree(d_sum);
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

    float *in      = (float *)malloc(N * sizeof(float));
    float *cpu_out = (float *)malloc(N * sizeof(float));
    float *gpu_out = (float *)malloc(N * sizeof(float));
    float cpu_sum = 0.0f, gpu_sum = 0.0f;

    fill_array(in, N, seed);
    cpu_pipeline(in, cpu_out, &cpu_sum, N);
    gpu_pipeline(in, gpu_out, &gpu_sum, N);

    int mismatches = 0;
    float max_err = 0.0f;
    for (int i = 0; i < N; i++) {
        float err = fabsf(cpu_out[i] - gpu_out[i]);
        if (err > max_err) max_err = err;
        if (err > 1e-4f) mismatches++;
    }

    float sum_err = fabsf(cpu_sum - gpu_sum) / (fabsf(cpu_sum) + 1e-12f);

    printf("N=%d\n", N);
    printf("CPU_SUM=%.4f\n", cpu_sum);
    printf("GPU_SUM=%.4f\n", gpu_sum);
    printf("SUM_REL_ERROR=%.6e\n", sum_err);
    printf("MISMATCHES=%d\n", mismatches);
    printf("MAX_ERROR=%.6e\n", max_err);
    printf("MATCH=%d\n", (mismatches == 0 && sum_err < 1e-3) ? 1 : 0);

    free(in); free(cpu_out); free(gpu_out);
    return (mismatches == 0 && sum_err < 1e-3) ? 0 : 1;
}
