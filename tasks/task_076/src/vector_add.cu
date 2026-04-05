#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define BLOCK_SIZE 256

/* ------------------------------------------------------------------ */
/* CPU reference (DO NOT MODIFY)                                      */
/* ------------------------------------------------------------------ */
void cpu_vector_add(const float *A, const float *B, float *C, int N) {
    for (int i = 0; i < N; i++) {
        C[i] = A[i] + B[i];
    }
}

/* ------------------------------------------------------------------ */
/* GPU kernel                                                          */
/* ------------------------------------------------------------------ */
__global__ void vector_add_kernel(const float *A, const float *B,
                                   float *C, int N) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    C[i] = A[i] + B[i];
}

/* ------------------------------------------------------------------ */
/* GPU driver                                                          */
/* ------------------------------------------------------------------ */
void gpu_vector_add(const float *h_A, const float *h_B, float *h_C, int N) {
    float *d_A, *d_B, *d_C;

    cudaMalloc(&d_A, N * sizeof(float));
    cudaMalloc(&d_B, N * sizeof(float));
    cudaMalloc(&d_C, N * sizeof(float));

    cudaMemcpy(d_A, h_A, N * sizeof(float), cudaMemcpyHostToDevice);
    cudaMemcpy(d_B, h_B, N * sizeof(float), cudaMemcpyHostToDevice);
    cudaMemset(d_C, 0, N * sizeof(float));

    int grid = N / BLOCK_SIZE;
    vector_add_kernel<<<grid, BLOCK_SIZE>>>(d_A, d_B, d_C, N);

    cudaDeviceSynchronize();
    cudaMemcpy(h_C, d_C, N * sizeof(float), cudaMemcpyDeviceToHost);

    cudaFree(d_A);
    cudaFree(d_B);
    cudaFree(d_C);
}

/* ------------------------------------------------------------------ */
/* Helpers                                                             */
/* ------------------------------------------------------------------ */
void fill_array(float *arr, int N, unsigned int seed) {
    for (int i = 0; i < N; i++) {
        seed = seed * 1103515245u + 12345u;
        arr[i] = (float)(seed % 10000) / 100.0f;
    }
}

/* ------------------------------------------------------------------ */
int main(int argc, char **argv) {
    int N = 1000;
    unsigned int seed = 42;

    for (int k = 1; k < argc; k++) {
        if (strcmp(argv[k], "--size") == 0 && k + 1 < argc) N = atoi(argv[++k]);
        else if (strcmp(argv[k], "--seed") == 0 && k + 1 < argc) seed = (unsigned int)atoi(argv[++k]);
    }

    float *A = (float *)malloc(N * sizeof(float));
    float *B = (float *)malloc(N * sizeof(float));
    float *cpu_C = (float *)malloc(N * sizeof(float));
    float *gpu_C = (float *)malloc(N * sizeof(float));

    fill_array(A, N, seed);
    fill_array(B, N, seed + 777);

    cpu_vector_add(A, B, cpu_C, N);
    gpu_vector_add(A, B, gpu_C, N);

    int mismatches = 0;
    float max_err = 0.0f;
    for (int i = 0; i < N; i++) {
        float err = fabsf(cpu_C[i] - gpu_C[i]);
        if (err > max_err) max_err = err;
        if (err > 1e-5f) mismatches++;
    }

    printf("N=%d\n", N);
    printf("BLOCK_SIZE=%d\n", BLOCK_SIZE);
    printf("MISMATCHES=%d\n", mismatches);
    printf("MAX_ERROR=%.6e\n", max_err);
    printf("MATCH=%d\n", mismatches == 0 ? 1 : 0);

    free(A); free(B); free(cpu_C); free(gpu_C);
    return mismatches == 0 ? 0 : 1;
}
