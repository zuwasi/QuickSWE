#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define BLOCK_SIZE 256
#define NUM_BINS   256

// ---------------------------------------------------------------------------
// BUG 1: Shared memory s_hist is never initialized to zero.
// BUG 2: __syncthreads() is missing between initialization and accumulation,
//         and between accumulation and the merge to global memory.
// ---------------------------------------------------------------------------
__global__ void histogram_kernel(const unsigned char *data, int N, int *hist) {
    __shared__ int s_hist[NUM_BINS];

    // BUG: No initialization of s_hist — shared memory contains garbage.
    // Should be:
    //   for (int bin = threadIdx.x; bin < NUM_BINS; bin += blockDim.x)
    //       s_hist[bin] = 0;
    //   __syncthreads();

    // Accumulate into shared histogram
    int tid = blockIdx.x * blockDim.x + threadIdx.x;
    int stride = blockDim.x * gridDim.x;
    for (int i = tid; i < N; i += stride) {
        atomicAdd(&s_hist[data[i]], 1);
    }

    // BUG: Missing __syncthreads() before merge — threads may still be
    // writing to s_hist while others start reading it.

    // Merge shared histogram into global histogram
    for (int bin = threadIdx.x; bin < NUM_BINS; bin += blockDim.x) {
        atomicAdd(&hist[bin], s_hist[bin]);
    }
}

// ---------------------------------------------------------------------------
// CPU reference histogram for verification
// ---------------------------------------------------------------------------
void cpu_histogram(const unsigned char *data, int N, int *hist) {
    memset(hist, 0, NUM_BINS * sizeof(int));
    for (int i = 0; i < N; i++) {
        hist[data[i]]++;
    }
}

// ---------------------------------------------------------------------------
// Simple LCG PRNG for deterministic data generation
// ---------------------------------------------------------------------------
static unsigned int lcg_state;

void lcg_seed(unsigned int seed) { lcg_state = seed; }

unsigned char lcg_next(void) {
    lcg_state = lcg_state * 1664525u + 1013904223u;
    return (unsigned char)((lcg_state >> 16) & 0xFF);
}

// ---------------------------------------------------------------------------
int main(int argc, char **argv) {
    int N = 1000;
    unsigned int seed = 42;

    for (int k = 1; k < argc; k++) {
        if (strcmp(argv[k], "--size") == 0 && k + 1 < argc) {
            N = atoi(argv[++k]);
        } else if (strcmp(argv[k], "--seed") == 0 && k + 1 < argc) {
            seed = (unsigned int)atoi(argv[++k]);
        }
    }

    // Generate deterministic input data
    unsigned char *h_data = (unsigned char *)malloc(N);
    if (!h_data) { fprintf(stderr, "ERROR: malloc\n"); return 1; }

    lcg_seed(seed);
    for (int i = 0; i < N; i++) {
        h_data[i] = lcg_next();
    }

    // CPU reference
    int cpu_hist[NUM_BINS];
    cpu_histogram(h_data, N, cpu_hist);

    // Device allocations
    unsigned char *d_data;
    int *d_hist;
    cudaError_t err;

    err = cudaMalloc(&d_data, N);
    if (err != cudaSuccess) { fprintf(stderr, "ERROR: cudaMalloc data: %s\n", cudaGetErrorString(err)); return 1; }

    err = cudaMalloc(&d_hist, NUM_BINS * sizeof(int));
    if (err != cudaSuccess) { fprintf(stderr, "ERROR: cudaMalloc hist: %s\n", cudaGetErrorString(err)); return 1; }

    cudaMemcpy(d_data, h_data, N, cudaMemcpyHostToDevice);
    cudaMemset(d_hist, 0, NUM_BINS * sizeof(int));

    // Launch kernel
    int grid = (N + BLOCK_SIZE - 1) / BLOCK_SIZE;
    if (grid > 256) grid = 256;  // cap grid size

    histogram_kernel<<<grid, BLOCK_SIZE>>>(d_data, N, d_hist);

    err = cudaGetLastError();
    if (err != cudaSuccess) { fprintf(stderr, "ERROR: kernel: %s\n", cudaGetErrorString(err)); return 1; }
    cudaDeviceSynchronize();

    // Copy result back
    int gpu_hist[NUM_BINS];
    cudaMemcpy(gpu_hist, d_hist, NUM_BINS * sizeof(int), cudaMemcpyDeviceToHost);

    // Compare and report
    int errors = 0;
    for (int bin = 0; bin < NUM_BINS; bin++) {
        if (gpu_hist[bin] != cpu_hist[bin]) {
            errors++;
        }
    }

    printf("SIZE=%d\n", N);
    printf("SEED=%u\n", seed);
    printf("ERRORS=%d\n", errors);

    for (int bin = 0; bin < NUM_BINS; bin++) {
        printf("BIN[%d] gpu=%d cpu=%d\n", bin, gpu_hist[bin], cpu_hist[bin]);
    }

    // Cleanup
    cudaFree(d_data);
    cudaFree(d_hist);
    free(h_data);

    return errors > 0 ? 1 : 0;
}
