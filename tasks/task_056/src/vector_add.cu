#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define BLOCK_SIZE 256

// BUG 1: Missing bounds check — when grid is rounded up, threads with i >= N
//        will read/write out of bounds.
// BUG 2: Grid dimension is computed without rounding up (see main).
__global__ void vector_add(const float *a, const float *b, float *c, int N) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    // BUG: No bounds check — should be: if (i < N)
    c[i] = a[i] + b[i];
}

int main(int argc, char **argv) {
    int N = 256;  // default: exact multiple of BLOCK_SIZE

    // Parse command-line arguments
    for (int k = 1; k < argc; k++) {
        if (strcmp(argv[k], "--size") == 0 && k + 1 < argc) {
            N = atoi(argv[k + 1]);
            k++;
        }
    }

    size_t bytes = N * sizeof(float);

    // Host allocations
    float *h_a = (float *)malloc(bytes);
    float *h_b = (float *)malloc(bytes);
    float *h_c = (float *)malloc(bytes);

    if (!h_a || !h_b || !h_c) {
        fprintf(stderr, "ERROR: Host allocation failed\n");
        return 1;
    }

    // Initialize host vectors
    for (int i = 0; i < N; i++) {
        h_a[i] = (float)i;
        h_b[i] = (float)(i * 2);
        h_c[i] = 0.0f;
    }

    // Device allocations
    float *d_a, *d_b, *d_c;
    cudaError_t err;

    err = cudaMalloc(&d_a, bytes);
    if (err != cudaSuccess) {
        fprintf(stderr, "ERROR: cudaMalloc d_a: %s\n", cudaGetErrorString(err));
        return 1;
    }
    err = cudaMalloc(&d_b, bytes);
    if (err != cudaSuccess) {
        fprintf(stderr, "ERROR: cudaMalloc d_b: %s\n", cudaGetErrorString(err));
        return 1;
    }
    err = cudaMalloc(&d_c, bytes);
    if (err != cudaSuccess) {
        fprintf(stderr, "ERROR: cudaMalloc d_c: %s\n", cudaGetErrorString(err));
        return 1;
    }

    // Copy input data to device
    cudaMemcpy(d_a, h_a, bytes, cudaMemcpyHostToDevice);
    cudaMemcpy(d_b, h_b, bytes, cudaMemcpyHostToDevice);
    cudaMemset(d_c, 0, bytes);

    // BUG: Grid computed without rounding up — truncates when N % BLOCK_SIZE != 0
    // For N=1000, BLOCK_SIZE=256: grid = 1000/256 = 3 (should be 4)
    // Only 768 elements are processed; elements 768-999 remain zero.
    int grid = N / BLOCK_SIZE;

    vector_add<<<grid, BLOCK_SIZE>>>(d_a, d_b, d_c, N);

    err = cudaGetLastError();
    if (err != cudaSuccess) {
        fprintf(stderr, "ERROR: Kernel launch: %s\n", cudaGetErrorString(err));
        return 1;
    }

    cudaDeviceSynchronize();

    // Copy result back
    cudaMemcpy(h_c, d_c, bytes, cudaMemcpyDeviceToHost);

    // Print results: one value per line as "index:value"
    int errors = 0;
    for (int i = 0; i < N; i++) {
        float expected = (float)(i + i * 2);
        if (h_c[i] != expected) {
            errors++;
        }
    }

    printf("SIZE=%d\n", N);
    printf("ERRORS=%d\n", errors);

    // Print individual results for detailed checking
    for (int i = 0; i < N; i++) {
        printf("RESULT[%d]=%.1f\n", i, h_c[i]);
    }

    // Cleanup
    cudaFree(d_a);
    cudaFree(d_b);
    cudaFree(d_c);
    free(h_a);
    free(h_b);
    free(h_c);

    return errors > 0 ? 1 : 0;
}
