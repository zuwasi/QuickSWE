#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

// ---------------------------------------------------------------------------
// CPU reference GEMM: C = A * B   (DO NOT MODIFY)
//   A is M×K, B is K×N, C is M×N   (row-major)
// ---------------------------------------------------------------------------
void cpu_gemm(const float *A, const float *B, float *C,
              int M, int N, int K) {
    for (int i = 0; i < M; i++) {
        for (int j = 0; j < N; j++) {
            double sum = 0.0;
            for (int p = 0; p < K; p++) {
                sum += (double)A[i * K + p] * (double)B[p * N + j];
            }
            C[i * N + j] = (float)sum;
        }
    }
}

// ---------------------------------------------------------------------------
// Naive GPU GEMM kernel  (DO NOT MODIFY)
// ---------------------------------------------------------------------------
__global__ void naive_gemm_kernel(const float *A, const float *B, float *C,
                                  int M, int N, int K) {
    int row = blockIdx.y * blockDim.y + threadIdx.y;
    int col = blockIdx.x * blockDim.x + threadIdx.x;
    if (row < M && col < N) {
        float sum = 0.0f;
        for (int p = 0; p < K; p++) {
            sum += A[row * K + p] * B[p * N + col];
        }
        C[row * N + col] = sum;
    }
}

// ---------------------------------------------------------------------------
// Tiled GEMM with register blocking — STUB (to be implemented)
// ---------------------------------------------------------------------------

// TODO: implement tiled GEMM kernel(s)
// Suggested parameters:
//   TILE_M = 32, TILE_N = 32, TILE_K = 32
//   THREAD_TILE_M = 4, THREAD_TILE_N = 4
//   → each block has (TILE_M/THREAD_TILE_M) × (TILE_N/THREAD_TILE_N) = 8×8 = 64 threads
//   → each thread accumulates a 4×4 register tile

void tiled_gemm(const float *h_A, const float *h_B, float *h_C,
                int M, int N, int K) {
    // TODO: implement tiled GEMM with shared memory + register blocking.
    // For now, falls back to the naive kernel.

    float *d_A, *d_B, *d_C;
    cudaMalloc(&d_A, M * K * sizeof(float));
    cudaMalloc(&d_B, K * N * sizeof(float));
    cudaMalloc(&d_C, M * N * sizeof(float));

    cudaMemcpy(d_A, h_A, M * K * sizeof(float), cudaMemcpyHostToDevice);
    cudaMemcpy(d_B, h_B, K * N * sizeof(float), cudaMemcpyHostToDevice);

    dim3 block(16, 16);
    dim3 grid((N + block.x - 1) / block.x, (M + block.y - 1) / block.y);
    naive_gemm_kernel<<<grid, block>>>(d_A, d_B, d_C, M, N, K);

    cudaMemcpy(h_C, d_C, M * N * sizeof(float), cudaMemcpyDeviceToHost);

    cudaFree(d_A);
    cudaFree(d_B);
    cudaFree(d_C);
}

// ---------------------------------------------------------------------------
// Main — structured output for test harness
// ---------------------------------------------------------------------------
int main(int argc, char **argv) {
    int M = 64, N = 64, K = 64;
    unsigned int seed = 42;
    int use_tiled = 1;

    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--M") == 0 && i + 1 < argc) M = atoi(argv[++i]);
        else if (strcmp(argv[i], "--N") == 0 && i + 1 < argc) N = atoi(argv[++i]);
        else if (strcmp(argv[i], "--K") == 0 && i + 1 < argc) K = atoi(argv[++i]);
        else if (strcmp(argv[i], "--seed") == 0 && i + 1 < argc)
            seed = (unsigned int)atoi(argv[++i]);
        else if (strcmp(argv[i], "--naive") == 0) use_tiled = 0;
    }

    float *A     = (float *)malloc(M * K * sizeof(float));
    float *B     = (float *)malloc(K * N * sizeof(float));
    float *C_cpu = (float *)malloc(M * N * sizeof(float));
    float *C_gpu = (float *)malloc(M * N * sizeof(float));
    if (!A || !B || !C_cpu || !C_gpu) {
        fprintf(stderr, "ERROR: malloc\n");
        return 1;
    }

    srand(seed);
    for (int i = 0; i < M * K; i++) A[i] = (float)(rand() % 100) / 50.0f - 1.0f;
    for (int i = 0; i < K * N; i++) B[i] = (float)(rand() % 100) / 50.0f - 1.0f;

    cpu_gemm(A, B, C_cpu, M, N, K);

    if (use_tiled) {
        tiled_gemm(A, B, C_gpu, M, N, K);
    } else {
        // Use naive via same host wrapper pattern
        float *d_A, *d_B, *d_C;
        cudaMalloc(&d_A, M * K * sizeof(float));
        cudaMalloc(&d_B, K * N * sizeof(float));
        cudaMalloc(&d_C, M * N * sizeof(float));
        cudaMemcpy(d_A, A, M * K * sizeof(float), cudaMemcpyHostToDevice);
        cudaMemcpy(d_B, B, K * N * sizeof(float), cudaMemcpyHostToDevice);
        dim3 block(16, 16);
        dim3 grid((N + 15) / 16, (M + 15) / 16);
        naive_gemm_kernel<<<grid, block>>>(d_A, d_B, d_C, M, N, K);
        cudaMemcpy(C_gpu, d_C, M * N * sizeof(float), cudaMemcpyDeviceToHost);
        cudaFree(d_A); cudaFree(d_B); cudaFree(d_C);
    }

    float max_err = 0.0f;
    int mismatches = 0;
    int first_bad = -1;
    for (int i = 0; i < M * N; i++) {
        float err = fabsf(C_cpu[i] - C_gpu[i]);
        if (err > max_err) max_err = err;
        if (err > 1e-2f) {
            if (first_bad < 0) first_bad = i;
            mismatches++;
        }
    }

    int match = (mismatches == 0) ? 1 : 0;

    printf("M=%d\n", M);
    printf("N=%d\n", N);
    printf("K=%d\n", K);
    printf("MODE=%s\n", use_tiled ? "TILED" : "NAIVE");
    printf("MAX_ERROR=%.6f\n", max_err);
    printf("MISMATCHES=%d\n", mismatches);
    if (first_bad >= 0) {
        int bad_row = first_bad / N;
        int bad_col = first_bad % N;
        printf("FIRST_BAD_ROW=%d\n", bad_row);
        printf("FIRST_BAD_COL=%d\n", bad_col);
        printf("EXPECTED=%.6f\n", C_cpu[first_bad]);
        printf("GOT=%.6f\n", C_gpu[first_bad]);
    }
    printf("MATCH=%d\n", match);

    free(A); free(B); free(C_cpu); free(C_gpu);
    return match ? 0 : 1;
}
