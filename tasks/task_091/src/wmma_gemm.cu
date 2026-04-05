#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <mma.h>
using namespace nvcuda;

#define WMMA_M 16
#define WMMA_N 16
#define WMMA_K 16

/* ------------------------------------------------------------------ */
/* CPU reference GEMM (DO NOT MODIFY)                                 */
/* ------------------------------------------------------------------ */
void cpu_gemm(const half *A, const half *B, float *C,
              int M, int N, int K) {
    for (int i = 0; i < M; i++) {
        for (int j = 0; j < N; j++) {
            float sum = 0.0f;
            for (int k = 0; k < K; k++) {
                sum += __half2float(A[i * K + k]) * __half2float(B[k * N + j]);
            }
            C[i * N + j] = sum;
        }
    }
}

/* ------------------------------------------------------------------ */
/* GPU WMMA kernel                                                     */
/* ------------------------------------------------------------------ */
__global__ void wmma_gemm_kernel(const half *A, const half *B, float *C,
                                   int M, int N, int K) {
    int warpM = (blockIdx.x * blockDim.x + threadIdx.x) / 32 * WMMA_M;
    int warpN = blockIdx.y * WMMA_N;

    if (warpM >= M || warpN >= N) return;

    wmma::fragment<wmma::accumulator, WMMA_M, WMMA_N, WMMA_K, float> c_frag;
    wmma::fill_fragment(c_frag, 0.0f);

    for (int k = 0; k < K; k += WMMA_K) {
        wmma::fragment<wmma::matrix_a, WMMA_M, WMMA_N, WMMA_K, half,
                       wmma::col_major> a_frag;
        wmma::fragment<wmma::matrix_b, WMMA_M, WMMA_N, WMMA_K, half,
                       wmma::col_major> b_frag;

        const half *a_ptr = A + warpM * K + k;
        const half *b_ptr = B + k * N + warpN;

        wmma::load_matrix_sync(a_frag, a_ptr, N);
        wmma::load_matrix_sync(b_frag, b_ptr, N);

        wmma::mma_sync(c_frag, a_frag, b_frag, c_frag);
    }

    float *c_ptr = C + warpM * N + warpN;
    wmma::store_matrix_sync(c_ptr, c_frag, N, wmma::mem_row_major);
}

/* ------------------------------------------------------------------ */
void gpu_gemm(const half *h_A, const half *h_B, float *h_C,
              int M, int N, int K) {
    half *d_A, *d_B;
    float *d_C;

    cudaMalloc(&d_A, M * K * sizeof(half));
    cudaMalloc(&d_B, K * N * sizeof(half));
    cudaMalloc(&d_C, M * N * sizeof(float));

    cudaMemcpy(d_A, h_A, M * K * sizeof(half), cudaMemcpyHostToDevice);
    cudaMemcpy(d_B, h_B, K * N * sizeof(half), cudaMemcpyHostToDevice);
    cudaMemset(d_C, 0, M * N * sizeof(float));

    dim3 block(128);
    dim3 grid((M + WMMA_M - 1) / WMMA_M * 32 / 128 + 1,
              (N + WMMA_N - 1) / WMMA_N);

    wmma_gemm_kernel<<<grid, block>>>(d_A, d_B, d_C, M, N, K);
    cudaDeviceSynchronize();

    cudaMemcpy(h_C, d_C, M * N * sizeof(float), cudaMemcpyDeviceToHost);
    cudaFree(d_A); cudaFree(d_B); cudaFree(d_C);
}

/* ------------------------------------------------------------------ */
void fill_half(half *arr, int size, unsigned int seed) {
    for (int i = 0; i < size; i++) {
        seed = seed * 1103515245u + 12345u;
        arr[i] = __float2half((float)(seed % 100) / 50.0f - 1.0f);
    }
}

int main(int argc, char **argv) {
    int M = 32, N = 32, K = 32;
    unsigned int seed = 42;

    for (int k = 1; k < argc; k++) {
        if (strcmp(argv[k], "--M") == 0 && k+1 < argc) M = atoi(argv[++k]);
        else if (strcmp(argv[k], "--N") == 0 && k+1 < argc) N = atoi(argv[++k]);
        else if (strcmp(argv[k], "--K") == 0 && k+1 < argc) K = atoi(argv[++k]);
        else if (strcmp(argv[k], "--seed") == 0 && k+1 < argc) seed = (unsigned int)atoi(argv[++k]);
    }

    half  *A = (half *)malloc(M * K * sizeof(half));
    half  *B = (half *)malloc(K * N * sizeof(half));
    float *cpu_C = (float *)malloc(M * N * sizeof(float));
    float *gpu_C = (float *)malloc(M * N * sizeof(float));

    fill_half(A, M * K, seed);
    fill_half(B, K * N, seed + 777);

    cpu_gemm(A, B, cpu_C, M, N, K);
    gpu_gemm(A, B, gpu_C, M, N, K);

    int mismatches = 0;
    float max_err = 0.0f;
    for (int i = 0; i < M * N; i++) {
        float err = fabsf(cpu_C[i] - gpu_C[i]);
        if (err > max_err) max_err = err;
        if (err > 1.0f) mismatches++;
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
