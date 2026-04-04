#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define BLOCK_SIZE 256
#define WARP_SIZE  32

// ---------------------------------------------------------------------------
// CPU reference reduction
// ---------------------------------------------------------------------------
double cpu_reduce(const float *data, int N) {
    double sum = 0.0;
    for (int i = 0; i < N; i++) {
        sum += (double)data[i];
    }
    return sum;
}

// ---------------------------------------------------------------------------
// Warp-level reduction using shuffle — BUGGY
// ---------------------------------------------------------------------------

/*
 * BUG 1: The mask is always 0xFFFFFFFF regardless of how many lanes are
 *         actually active in the last warp of each block.  When N is not a
 *         multiple of WARP_SIZE the inactive lanes contribute undefined
 *         values to the shuffle.
 *
 * BUG 2: The reduction width is hardcoded to WARP_SIZE (32).  For the
 *         partial last warp the width should equal the number of active
 *         lanes so that __shfl_down_sync wraps correctly.
 *
 * BUG 3: The per-warp partial sums are combined with a simple global-memory
 *         write (output[warpId]) instead of atomicAdd, so warps from
 *         different blocks that share the same warpId silently overwrite
 *         each other.
 */

__global__ void warp_reduce_kernel(const float *input, float *output, int N) {
    int tid = blockIdx.x * blockDim.x + threadIdx.x;

    // Each thread loads one element (or 0 if out of bounds)
    float val = (tid < N) ? input[tid] : 0.0f;

    // --- Warp-level reduction via shuffle ---
    // BUG 1 & 2: full mask and full width even for partial warps
    unsigned mask = 0xFFFFFFFF;
    for (int offset = WARP_SIZE / 2; offset > 0; offset >>= 1) {
        val += __shfl_down_sync(mask, val, offset, WARP_SIZE);
    }

    // Lane 0 of each warp writes its result
    int laneId = threadIdx.x % WARP_SIZE;
    int warpId = threadIdx.x / WARP_SIZE;

    // Shared memory to collect per-warp sums within a block
    __shared__ float warp_sums[BLOCK_SIZE / WARP_SIZE];

    if (laneId == 0) {
        warp_sums[warpId] = val;
    }
    __syncthreads();

    // First warp in the block reduces the warp_sums
    if (warpId == 0) {
        float v = (laneId < (BLOCK_SIZE / WARP_SIZE)) ? warp_sums[laneId] : 0.0f;
        for (int offset = WARP_SIZE / 2; offset > 0; offset >>= 1) {
            v += __shfl_down_sync(0xFFFFFFFF, v, offset, WARP_SIZE);
        }
        if (laneId == 0) {
            // BUG 3: non-atomic write — blocks with the same index overwrite
            output[blockIdx.x] = v;
        }
    }
}

// ---------------------------------------------------------------------------
// Host-side reduction driver — BUGGY
// ---------------------------------------------------------------------------
double gpu_reduce(const float *h_data, int N) {
    float *d_input  = NULL;
    float *d_output = NULL;

    int gridSize = (N + BLOCK_SIZE - 1) / BLOCK_SIZE;

    cudaMalloc(&d_input,  N * sizeof(float));
    cudaMalloc(&d_output, gridSize * sizeof(float));
    cudaMemcpy(d_input, h_data, N * sizeof(float), cudaMemcpyHostToDevice);
    cudaMemset(d_output, 0, gridSize * sizeof(float));

    warp_reduce_kernel<<<gridSize, BLOCK_SIZE>>>(d_input, d_output, N);

    // Second pass: reduce the per-block results on the GPU
    float *d_final = NULL;
    int gridSize2 = (gridSize + BLOCK_SIZE - 1) / BLOCK_SIZE;
    cudaMalloc(&d_final, gridSize2 * sizeof(float));
    cudaMemset(d_final, 0, gridSize2 * sizeof(float));

    warp_reduce_kernel<<<gridSize2, BLOCK_SIZE>>>(d_output, d_final, gridSize);

    // Copy back and sum remaining values on CPU
    float *h_partial = (float *)malloc(gridSize2 * sizeof(float));
    cudaMemcpy(h_partial, d_final, gridSize2 * sizeof(float), cudaMemcpyDeviceToHost);

    double total = 0.0;
    for (int i = 0; i < gridSize2; i++) {
        total += (double)h_partial[i];
    }

    free(h_partial);
    cudaFree(d_input);
    cudaFree(d_output);
    cudaFree(d_final);
    return total;
}

// ---------------------------------------------------------------------------
// Main — structured output for test harness
// ---------------------------------------------------------------------------
int main(int argc, char **argv) {
    int N = 1024;
    unsigned int seed = 42;

    for (int k = 1; k < argc; k++) {
        if (strcmp(argv[k], "--size") == 0 && k + 1 < argc) {
            N = atoi(argv[++k]);
        } else if (strcmp(argv[k], "--seed") == 0 && k + 1 < argc) {
            seed = (unsigned int)atoi(argv[++k]);
        }
    }

    float *data = (float *)malloc(N * sizeof(float));
    if (!data) { fprintf(stderr, "ERROR: malloc\n"); return 1; }

    srand(seed);
    for (int i = 0; i < N; i++) {
        data[i] = (float)(rand() % 10000) / 100.0f;
    }

    double cpu_sum = cpu_reduce(data, N);
    double gpu_sum = gpu_reduce(data, N);
    double absdiff = fabs(cpu_sum - gpu_sum);
    // Allow small floating-point tolerance scaled by N
    double tol = (double)N * 1e-2;
    int match = (absdiff <= tol) ? 1 : 0;

    printf("SIZE=%d\n", N);
    printf("CPU_SUM=%.6f\n", cpu_sum);
    printf("GPU_SUM=%.6f\n", gpu_sum);
    printf("ABSDIFF=%.6f\n", absdiff);
    printf("TOLERANCE=%.6f\n", tol);
    printf("MATCH=%d\n", match);

    free(data);
    return match ? 0 : 1;
}
