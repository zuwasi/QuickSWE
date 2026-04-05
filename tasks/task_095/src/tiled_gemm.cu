#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define TILE_SIZE 16

/* ------------------------------------------------------------------ */
/* CPU reference (DO NOT MODIFY)                                      */
/* ------------------------------------------------------------------ */
void cpu_gemm(const float *A, const float *B, float *C,
              int M, int N, int K) {
    for (int i = 0; i < M; i++)
        for (int j = 0; j < N; j++) {
            float sum = 0.0f;
            for (int k = 0; k < K; k++)
                sum += A[i * K + k] * B[k * N + j];
            C[i * N + j] = sum;
        }
}

/* ------------------------------------------------------------------ */
/* GPU tiled GEMM kernel with double buffering                         */
/* ------------------------------------------------------------------ */
__global__ void tiled_gemm_kernel(const float *A, const float *B, float *C,
                                    int M, int N, int K) {
    __shared__ float As[2][TILE_SIZE][TILE_SIZE];
    __shared__ float Bs[2][TILE_SIZE][TILE_SIZE];

    int tx = threadIdx.x;
    int ty = threadIdx.y;
    int row = blockIdx.y * TILE_SIZE + ty;
    int col = blockIdx.x * TILE_SIZE + tx;

    float sum = 0.0f;
    int num_tiles = (K + TILE_SIZE - 1) / TILE_SIZE;

    int write_buf = 0;

    /* Load first tile */
    int a_col = 0 * TILE_SIZE + tx;
    int b_row = 0 * TILE_SIZE + ty;
    As[write_buf][ty][tx] = (row < M && a_col < K) ? A[row * K + a_col] : 0.0f;
    Bs[write_buf][ty][tx] = (b_row < K && col < N) ? B[b_row * N + col] : 0.0f;
    __syncthreads();

    for (int t = 0; t < num_tiles; t++) {
        int read_buf = write_buf;
        write_buf = 1 - write_buf;

        /* Prefetch next tile into write buffer */
        if (t + 1 < num_tiles) {
            int next_a_col = (t + 1) * TILE_SIZE + tx;
            int next_b_row = (t + 1) * TILE_SIZE + ty;
            As[read_buf][ty][tx] = (row < M && next_a_col < K) ?
                A[row * K + next_a_col] : 0.0f;
            Bs[read_buf][ty][tx] = (next_b_row < K && col < N) ?
                B[next_b_row * N + col] : 0.0f;
        }

        /* Compute on read buffer — but we just overwrote read_buf above! */
        for (int k = 0; k < TILE_SIZE; k++) {
            sum += As[read_buf][ty][k] * Bs[read_buf][k][tx];
        }

        __syncthreads();
    }

    if (row < M && col < N) {
        C[row * N + col] = sum;
    }
}

/* ------------------------------------------------------------------ */
void gpu_gemm(const float *h_A, const float *h_B, float *h_C,
              int M, int N, int K) {
    float *d_A, *d_B, *d_C;

    cudaMalloc(&d_A, M * K * sizeof(float));
    cudaMalloc(&d_B, K * N * sizeof(float));
    cudaMalloc(&d_C, M * N * sizeof(float));

    cudaMemcpy(d_A, h_A, M * K * sizeof(float), cudaMemcpyHostToDevice);
    cudaMemcpy(d_B, h_B, K * N * sizeof(float), cudaMemcpyHostToDevice);
    cudaMemset(d_C, 0, M * N * sizeof(float));

    dim3 block(TILE_SIZE, TILE_SIZE);
    dim3 grid((N + TILE_SIZE - 1) / TILE_SIZE,
              (M + TILE_SIZE - 1) / TILE_SIZE);

    tiled_gemm_kernel<<<grid, block>>>(d_A, d_B, d_C, M, N, K);
    cudaDeviceSynchronize();

    cudaMemcpy(h_C, d_C, M * N * sizeof(float), cudaMemcpyDeviceToHost);
    cudaFree(d_A); cudaFree(d_B); cudaFree(d_C);
}

/* ------------------------------------------------------------------ */
void fill_matrix(float *m, int size, unsigned int seed) {
    for (int i = 0; i < size; i++) {
        seed = seed * 1103515245u + 12345u;
        m[i] = (float)(seed % 100) / 50.0f - 1.0f;
    }
}

int main(int argc, char **argv) {
    int M = 64, N = 64, K = 64;
    unsigned int seed = 42;

    for (int k = 1; k < argc; k++) {
        if (strcmp(argv[k], "--M") == 0 && k+1 < argc) M = atoi(argv[++k]);
        else if (strcmp(argv[k], "--N") == 0 && k+1 < argc) N = atoi(argv[++k]);
        else if (strcmp(argv[k], "--K") == 0 && k+1 < argc) K = atoi(argv[++k]);
        else if (strcmp(argv[k], "--seed") == 0 && k+1 < argc) seed = (unsigned int)atoi(argv[++k]);
    }

    float *A = (float *)malloc(M * K * sizeof(float));
    float *B = (float *)malloc(K * N * sizeof(float));
    float *cpu_C = (float *)malloc(M * N * sizeof(float));
    float *gpu_C = (float *)malloc(M * N * sizeof(float));

    fill_matrix(A, M * K, seed);
    fill_matrix(B, K * N, seed + 777);

    cpu_gemm(A, B, cpu_C, M, N, K);
    gpu_gemm(A, B, gpu_C, M, N, K);

    int mismatches = 0;
    float max_err = 0.0f;
    for (int i = 0; i < M * N; i++) {
        float err = fabsf(cpu_C[i] - gpu_C[i]);
        if (err > max_err) max_err = err;
        if (err > 0.1f) mismatches++;
    }

    printf("M=%d\n", M);
    printf("N=%d\n", N);
    printf("K=%d\n", K);
    printf("MISMATCHES=%d\n", mismatches);
    printf("MAX_ERROR=%.6e\n", max_err);
    printf("MATCH=%d\n", mismatches == 0 ? 1 : 0);

    free(A); free(B); free(cpu_C); free(gpu_C);
    return mismatches == 0 ? 0 : 1;
}
