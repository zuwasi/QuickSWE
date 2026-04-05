#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define BLOCK_SIZE 128
#define NUM_BLOCKS 4

/* ------------------------------------------------------------------ */
/* CPU reference (DO NOT MODIFY)                                      */
/* ------------------------------------------------------------------ */
void cpu_process(const float *in, float *out, int N) {
    for (int i = 0; i < N; i++) {
        float v = in[i];
        out[i] = sqrtf(v * v + 1.0f) + sinf(v) * 0.5f;
    }
}

/* ------------------------------------------------------------------ */
/* GPU persistent kernel                                               */
/* ------------------------------------------------------------------ */
__global__ void persistent_process_kernel(const float *in, float *out,
                                            int N, int *work_counter) {
    int tid = blockIdx.x * blockDim.x + threadIdx.x;

    while (tid < N) {
        float v = in[tid];
        out[tid] = sqrtf(v * v + 1.0f) + sinf(v) * 0.5f;

        /* Grid-stride loop — increment is wrong */
        tid += blockDim.x;
    }
}

/* ------------------------------------------------------------------ */
void gpu_process(const float *h_in, float *h_out, int N) {
    float *d_in, *d_out;
    int *d_counter;

    cudaMalloc(&d_in,  N * sizeof(float));
    cudaMalloc(&d_out, N * sizeof(float));
    cudaMalloc(&d_counter, sizeof(int));

    cudaMemcpy(d_in, h_in, N * sizeof(float), cudaMemcpyHostToDevice);
    cudaMemset(d_out, 0, N * sizeof(float));
    cudaMemset(d_counter, 0, sizeof(int));

    persistent_process_kernel<<<NUM_BLOCKS, BLOCK_SIZE>>>(
        d_in, d_out, N, d_counter);
    cudaDeviceSynchronize();

    cudaMemcpy(h_out, d_out, N * sizeof(float), cudaMemcpyDeviceToHost);

    cudaFree(d_in); cudaFree(d_out); cudaFree(d_counter);
}

/* ------------------------------------------------------------------ */
void fill_array(float *arr, int N, unsigned int seed) {
    for (int i = 0; i < N; i++) {
        seed = seed * 1103515245u + 12345u;
        arr[i] = (float)(seed % 10000) / 1000.0f;
    }
}

int main(int argc, char **argv) {
    int N = 5000;
    unsigned int seed = 42;

    for (int k = 1; k < argc; k++) {
        if (strcmp(argv[k], "--size") == 0 && k+1 < argc) N = atoi(argv[++k]);
        else if (strcmp(argv[k], "--seed") == 0 && k+1 < argc) seed = (unsigned int)atoi(argv[++k]);
    }

    float *in      = (float *)malloc(N * sizeof(float));
    float *cpu_out = (float *)malloc(N * sizeof(float));
    float *gpu_out = (float *)malloc(N * sizeof(float));

    fill_array(in, N, seed);
    cpu_process(in, cpu_out, N);
    gpu_process(in, gpu_out, N);

    int mismatches = 0;
    int zeros = 0;
    float max_err = 0.0f;
    for (int i = 0; i < N; i++) {
        float err = fabsf(cpu_out[i] - gpu_out[i]);
        if (err > max_err) max_err = err;
        if (err > 0.001f) mismatches++;
        if (fabsf(gpu_out[i]) < 1e-10f) zeros++;
    }

    printf("N=%d\n", N);
    printf("BLOCKS=%d\n", NUM_BLOCKS);
    printf("MISMATCHES=%d\n", mismatches);
    printf("ZEROS=%d\n", zeros);
    printf("MAX_ERROR=%.6e\n", max_err);
    printf("MATCH=%d\n", mismatches == 0 ? 1 : 0);

    free(in); free(cpu_out); free(gpu_out);
    return mismatches == 0 ? 0 : 1;
}
