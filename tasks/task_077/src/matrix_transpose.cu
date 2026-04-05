#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define TILE_SIZE 16

/* ------------------------------------------------------------------ */
/* CPU reference (DO NOT MODIFY)                                      */
/* ------------------------------------------------------------------ */
void cpu_transpose(const float *in, float *out, int rows, int cols) {
    for (int r = 0; r < rows; r++)
        for (int c = 0; c < cols; c++)
            out[c * rows + r] = in[r * cols + c];
}

/* ------------------------------------------------------------------ */
/* GPU kernel                                                          */
/* ------------------------------------------------------------------ */
__global__ void transpose_kernel(const float *in, float *out,
                                  int rows, int cols) {
    __shared__ float tile[TILE_SIZE][TILE_SIZE];

    int bx = blockIdx.x * TILE_SIZE;
    int by = blockIdx.y * TILE_SIZE;

    int ix = bx + threadIdx.x;
    int iy = by + threadIdx.y;

    if (ix < cols && iy < rows) {
        tile[threadIdx.y][threadIdx.x] = in[iy * cols + ix];
    }

    __syncthreads();

    int ox = by + threadIdx.x;
    int oy = bx + threadIdx.y;

    if (ox < rows && oy < cols) {
        out[oy * rows + ox] = tile[threadIdx.x][threadIdx.y];
    }
}

/* ------------------------------------------------------------------ */
/* GPU driver                                                          */
/* ------------------------------------------------------------------ */
void gpu_transpose(const float *h_in, float *h_out, int rows, int cols) {
    float *d_in, *d_out;
    size_t in_sz  = rows * cols * sizeof(float);
    size_t out_sz = cols * rows * sizeof(float);

    cudaMalloc(&d_in,  in_sz);
    cudaMalloc(&d_out, out_sz);
    cudaMemcpy(d_in, h_in, in_sz, cudaMemcpyHostToDevice);
    cudaMemset(d_out, 0, out_sz);

    dim3 block(TILE_SIZE, TILE_SIZE);
    dim3 grid((cols + TILE_SIZE - 1) / TILE_SIZE,
              (rows + TILE_SIZE - 1) / TILE_SIZE);

    transpose_kernel<<<grid, block>>>(d_in, d_out, rows, cols);
    cudaDeviceSynchronize();

    cudaMemcpy(h_out, d_out, out_sz, cudaMemcpyDeviceToHost);
    cudaFree(d_in);
    cudaFree(d_out);
}

/* ------------------------------------------------------------------ */
void fill_matrix(float *m, int size, unsigned int seed) {
    for (int i = 0; i < size; i++) {
        seed = seed * 1103515245u + 12345u;
        m[i] = (float)(seed % 10000) / 100.0f;
    }
}

int main(int argc, char **argv) {
    int rows = 64, cols = 48;
    unsigned int seed = 42;

    for (int k = 1; k < argc; k++) {
        if (strcmp(argv[k], "--rows") == 0 && k+1 < argc) rows = atoi(argv[++k]);
        else if (strcmp(argv[k], "--cols") == 0 && k+1 < argc) cols = atoi(argv[++k]);
        else if (strcmp(argv[k], "--seed") == 0 && k+1 < argc) seed = (unsigned int)atoi(argv[++k]);
    }

    int total = rows * cols;
    float *in     = (float *)malloc(total * sizeof(float));
    float *cpu_out = (float *)malloc(total * sizeof(float));
    float *gpu_out = (float *)malloc(total * sizeof(float));

    fill_matrix(in, total, seed);
    cpu_transpose(in, cpu_out, rows, cols);
    gpu_transpose(in, gpu_out, rows, cols);

    int mismatches = 0;
    float max_err = 0.0f;
    for (int i = 0; i < total; i++) {
        float err = fabsf(cpu_out[i] - gpu_out[i]);
        if (err > max_err) max_err = err;
        if (err > 1e-5f) mismatches++;
    }

    printf("ROWS=%d\n", rows);
    printf("COLS=%d\n", cols);
    printf("MISMATCHES=%d\n", mismatches);
    printf("MAX_ERROR=%.6e\n", max_err);
    printf("MATCH=%d\n", mismatches == 0 ? 1 : 0);

    free(in); free(cpu_out); free(gpu_out);
    return mismatches == 0 ? 0 : 1;
}
