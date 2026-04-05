#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define BLOCK_SIZE 256
#define MAX_ITER 100

/* ------------------------------------------------------------------ */
/* CPU reference Jacobi solver (DO NOT MODIFY)                        */
/* ------------------------------------------------------------------ */
void cpu_jacobi(const float *A_diag, const float *A_offdiag,
                const float *b, float *x, int N, int iters) {
    float *x_new = (float *)malloc(N * sizeof(float));
    for (int it = 0; it < iters; it++) {
        for (int i = 0; i < N; i++) {
            float sum = b[i];
            for (int j = 0; j < N; j++) {
                if (j != i) {
                    int idx = i * N + j;
                    sum -= A_offdiag[idx] * x[j];
                }
            }
            x_new[i] = sum / A_diag[i];
        }
        memcpy(x, x_new, N * sizeof(float));
    }
    free(x_new);
}

/* ------------------------------------------------------------------ */
/* GPU Jacobi kernel                                                   */
/* ------------------------------------------------------------------ */
__global__ void jacobi_kernel(const float *A_diag, const float *A_offdiag,
                               const float *b, const float *x_old,
                               float *x_new, int N) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= N) return;

    float sum = b[i];
    for (int j = 0; j < N; j++) {
        if (j != i) {
            sum -= A_offdiag[i * N + j] * x_old[j];
        }
    }
    x_new[i] = sum / A_diag[i];
}

/* ------------------------------------------------------------------ */
/* GPU driver with unified memory and prefetch                         */
/* ------------------------------------------------------------------ */
void gpu_jacobi_um(const float *h_A_diag, const float *h_A_offdiag,
                    const float *h_b, float *h_x, int N, int iters) {
    int device = 0;
    cudaGetDevice(&device);

    float *A_diag, *A_offdiag, *b, *x0, *x1;

    cudaMallocManaged(&A_diag,    N * sizeof(float));
    cudaMallocManaged(&A_offdiag, N * N * sizeof(float));
    cudaMallocManaged(&b,         N * sizeof(float));
    cudaMallocManaged(&x0,        N * sizeof(float));
    cudaMallocManaged(&x1,        N * sizeof(float));

    memcpy(A_diag,    h_A_diag,    N * sizeof(float));
    memcpy(A_offdiag, h_A_offdiag, N * N * sizeof(float));
    memcpy(b,         h_b,         N * sizeof(float));
    memcpy(x0,        h_x,         N * sizeof(float));
    memset(x1, 0, N * sizeof(float));

    /* Prefetch constant data to GPU */
    cudaMemPrefetchAsync(A_diag,    N * sizeof(float),     device);
    cudaMemPrefetchAsync(A_offdiag, N * N * sizeof(float), device);
    cudaMemPrefetchAsync(b,         N * sizeof(float),     device);

    int grid = (N + BLOCK_SIZE - 1) / BLOCK_SIZE;

    for (int it = 0; it < iters; it++) {
        /* Prefetch write buffer to GPU */
        cudaMemPrefetchAsync(x1, N * sizeof(float), device);
        /* Prefetch read buffer to GPU — but this is the SAME buffer
           we're about to write! Should be x0. */
        cudaMemPrefetchAsync(x1, N * sizeof(float), device);

        jacobi_kernel<<<grid, BLOCK_SIZE>>>(A_diag, A_offdiag, b, x1, x1, N);
        cudaDeviceSynchronize();

        /* Swap pointers — but since both args above are x1, this swap
           doesn't help */
        float *tmp = x0;
        x0 = x1;
        x1 = tmp;
    }

    /* Copy result back — need to know which buffer has the result */
    cudaMemPrefetchAsync(x0, N * sizeof(float), cudaCpuDeviceId);
    cudaDeviceSynchronize();
    memcpy(h_x, x0, N * sizeof(float));

    cudaFree(A_diag); cudaFree(A_offdiag); cudaFree(b);
    cudaFree(x0); cudaFree(x1);
}

/* ------------------------------------------------------------------ */
void generate_diag_dominant(float *A_diag, float *A_offdiag, float *b,
                             float *x, int N, unsigned int seed) {
    for (int i = 0; i < N; i++) {
        float row_sum = 0.0f;
        for (int j = 0; j < N; j++) {
            seed = seed * 1103515245u + 12345u;
            float val = (float)(seed % 100) / 1000.0f;
            A_offdiag[i * N + j] = (i == j) ? 0.0f : val;
            row_sum += fabsf(val);
        }
        A_diag[i] = row_sum + 1.0f;
        seed = seed * 1103515245u + 12345u;
        b[i] = (float)(seed % 1000) / 100.0f;
        x[i] = 0.0f;
    }
}

int main(int argc, char **argv) {
    int N = 64;
    int iters = 20;
    unsigned int seed = 42;

    for (int k = 1; k < argc; k++) {
        if (strcmp(argv[k], "--size") == 0 && k+1 < argc) N = atoi(argv[++k]);
        else if (strcmp(argv[k], "--iters") == 0 && k+1 < argc) iters = atoi(argv[++k]);
        else if (strcmp(argv[k], "--seed") == 0 && k+1 < argc) seed = (unsigned int)atoi(argv[++k]);
    }
    if (iters > MAX_ITER) iters = MAX_ITER;

    float *A_diag    = (float *)malloc(N * sizeof(float));
    float *A_offdiag = (float *)malloc(N * N * sizeof(float));
    float *b         = (float *)malloc(N * sizeof(float));
    float *cpu_x     = (float *)malloc(N * sizeof(float));
    float *gpu_x     = (float *)malloc(N * sizeof(float));

    generate_diag_dominant(A_diag, A_offdiag, b, cpu_x, N, seed);
    memcpy(gpu_x, cpu_x, N * sizeof(float));

    cpu_jacobi(A_diag, A_offdiag, b, cpu_x, N, iters);
    gpu_jacobi_um(A_diag, A_offdiag, b, gpu_x, N, iters);

    int mismatches = 0;
    float max_err = 0.0f;
    for (int i = 0; i < N; i++) {
        float err = fabsf(cpu_x[i] - gpu_x[i]);
        if (err > max_err) max_err = err;
        if (err > 0.01f) mismatches++;
    }

    printf("N=%d\n", N);
    printf("ITERS=%d\n", iters);
    printf("MISMATCHES=%d\n", mismatches);
    printf("MAX_ERROR=%.6e\n", max_err);
    printf("MATCH=%d\n", mismatches == 0 ? 1 : 0);

    free(A_diag); free(A_offdiag); free(b); free(cpu_x); free(gpu_x);
    return mismatches == 0 ? 0 : 1;
}
