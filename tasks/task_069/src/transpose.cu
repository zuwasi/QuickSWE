#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define TILE_SIZE 32

// ---------------------------------------------------------------------------
// CPU reference transpose (DO NOT MODIFY)
// ---------------------------------------------------------------------------
void cpu_transpose(const float *in, float *out, int M, int N) {
    // in is M×N  (row-major), out is N×M
    for (int r = 0; r < M; r++) {
        for (int c = 0; c < N; c++) {
            out[c * M + r] = in[r * N + c];
        }
    }
}

// ---------------------------------------------------------------------------
// CUDA transpose kernel — BUGGY
// ---------------------------------------------------------------------------
__global__ void transpose_kernel(const float *in, float *out, int M, int N) {
    // BUG 1: no +1 padding → bank conflicts on column access
    __shared__ float tile[TILE_SIZE][TILE_SIZE];

    int in_x = blockIdx.x * TILE_SIZE + threadIdx.x;
    int in_y = blockIdx.y * TILE_SIZE + threadIdx.y;

    // Load tile from input (M×N)
    if (in_x < N && in_y < M) {
        tile[threadIdx.y][threadIdx.x] = in[in_y * N + in_x];
    }
    __syncthreads();

    // BUG 2: threadIdx.x and threadIdx.y are swapped for the output indices
    int out_x = blockIdx.y * TILE_SIZE + threadIdx.y;   // WRONG: should use threadIdx.x
    int out_y = blockIdx.x * TILE_SIZE + threadIdx.x;   // WRONG: should use threadIdx.y
    if (out_x < M && out_y < N) {
        out[out_y * M + out_x] = tile[threadIdx.x][threadIdx.y];
    }
}

// ---------------------------------------------------------------------------
// GPU transpose wrapper
// ---------------------------------------------------------------------------
void gpu_transpose(const float *h_in, float *h_out, int M, int N) {
    float *d_in, *d_out;
    cudaMalloc(&d_in, M * N * sizeof(float));
    cudaMalloc(&d_out, N * M * sizeof(float));
    cudaMemcpy(d_in, h_in, M * N * sizeof(float), cudaMemcpyHostToDevice);

    dim3 block(TILE_SIZE, TILE_SIZE);
    dim3 grid((N + TILE_SIZE - 1) / TILE_SIZE, (M + TILE_SIZE - 1) / TILE_SIZE);

    transpose_kernel<<<grid, block>>>(d_in, d_out, M, N);
    cudaDeviceSynchronize();

    cudaMemcpy(h_out, d_out, N * M * sizeof(float), cudaMemcpyDeviceToHost);
    cudaFree(d_in);
    cudaFree(d_out);
}

// ---------------------------------------------------------------------------
int main(int argc, char **argv) {
    int M = 64, N = 128;
    unsigned int seed = 42;

    for (int k = 1; k < argc; k++) {
        if (strcmp(argv[k], "--rows") == 0 && k + 1 < argc) {
            M = atoi(argv[++k]);
        } else if (strcmp(argv[k], "--cols") == 0 && k + 1 < argc) {
            N = atoi(argv[++k]);
        } else if (strcmp(argv[k], "--seed") == 0 && k + 1 < argc) {
            seed = (unsigned int)atoi(argv[++k]);
        }
    }

    float *in  = (float *)malloc(M * N * sizeof(float));
    float *cpu_out = (float *)malloc(N * M * sizeof(float));
    float *gpu_out = (float *)malloc(N * M * sizeof(float));
    if (!in || !cpu_out || !gpu_out) {
        fprintf(stderr, "ERROR: malloc\n");
        return 1;
    }

    srand(seed);
    for (int i = 0; i < M * N; i++) {
        in[i] = (float)(rand() % 1000) / 10.0f;
    }

    cpu_transpose(in, cpu_out, M, N);
    gpu_transpose(in, gpu_out, M, N);

    // Compare element-wise
    int mismatches = 0;
    for (int i = 0; i < N * M; i++) {
        if (cpu_out[i] != gpu_out[i]) {
            mismatches++;
        }
    }

    printf("ROWS=%d\n", M);
    printf("COLS=%d\n", N);
    printf("TOTAL_ELEMENTS=%d\n", M * N);
    printf("MISMATCHES=%d\n", mismatches);
    printf("MATCH=%d\n", mismatches == 0 ? 1 : 0);

    free(in);
    free(cpu_out);
    free(gpu_out);
    return mismatches == 0 ? 0 : 1;
}
