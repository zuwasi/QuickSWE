#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define BLOCK_SIZE 256

// ---------------------------------------------------------------------------
// CPU reference: square each element
// ---------------------------------------------------------------------------
void cpu_square(const float *in, float *out, int N) {
    for (int i = 0; i < N; i++) {
        out[i] = in[i] * in[i];
    }
}

// ---------------------------------------------------------------------------
// GPU kernel: square each element
// ---------------------------------------------------------------------------
__global__ void square_kernel(const float *in, float *out, int N) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < N) {
        out[idx] = in[idx] * in[idx];
    }
}

// ---------------------------------------------------------------------------
// Multi-stream processing driver — BUGGY
// ---------------------------------------------------------------------------

/*
 * We partition the array into two halves and process them in separate CUDA
 * streams.  Each stream: async-copies its partition to the device, runs the
 * kernel, async-copies results back.
 *
 * BUG 1 — Off-by-one overlap:
 *   partition 0 covers [0 .. mid]  (mid INCLUSIVE)
 *   partition 1 covers [mid .. N)  (mid INCLUSIVE again)
 *   So element at index `mid` is processed twice and the output slot is
 *   written by both kernels — one result overwrites the other, and the
 *   total element count is wrong.
 *
 * BUG 2 — Missing synchronisation:
 *   The kernel is launched right after cudaMemcpyAsync, but without
 *   waiting for the copy to finish.  Because we use the DEFAULT stream
 *   for the memcpy and a NON-default stream for the kernel, the kernel
 *   may start before the data has arrived, reading uninitialised device
 *   memory.
 *
 * BUG 3 — Result copy-back uses wrong size:
 *   Partition 1's result is copied with size_0 bytes instead of size_1
 *   bytes, so if the array is odd-length the last element is missing.
 */

void gpu_square_multistream(const float *h_in, float *h_out, int N) {
    cudaStream_t stream0, stream1;
    cudaStreamCreate(&stream0);
    cudaStreamCreate(&stream1);

    int mid = N / 2;

    // Partition sizes — BUG 1: overlap at mid
    int size_0 = mid + 1;           // [0 .. mid] inclusive  <-- should be mid
    int size_1 = N - mid;           // [mid .. N-1]          <-- should be N - mid

    float *d_in0,  *d_out0;
    float *d_in1,  *d_out1;
    cudaMalloc(&d_in0,  size_0 * sizeof(float));
    cudaMalloc(&d_out0, size_0 * sizeof(float));
    cudaMalloc(&d_in1,  size_1 * sizeof(float));
    cudaMalloc(&d_out1, size_1 * sizeof(float));

    // ---------- Partition 0 ----------
    // BUG 2: copy on default stream (0), kernel on stream0
    //         → no guarantee copy finishes before kernel reads
    cudaMemcpyAsync(d_in0, h_in, size_0 * sizeof(float),
                    cudaMemcpyHostToDevice, (cudaStream_t)0);

    int grid0 = (size_0 + BLOCK_SIZE - 1) / BLOCK_SIZE;
    square_kernel<<<grid0, BLOCK_SIZE, 0, stream0>>>(d_in0, d_out0, size_0);

    // ---------- Partition 1 ----------
    // BUG 2 again: copy on default stream, kernel on stream1
    cudaMemcpyAsync(d_in1, h_in + mid, size_1 * sizeof(float),
                    cudaMemcpyHostToDevice, (cudaStream_t)0);

    int grid1 = (size_1 + BLOCK_SIZE - 1) / BLOCK_SIZE;
    square_kernel<<<grid1, BLOCK_SIZE, 0, stream1>>>(d_in1, d_out1, size_1);

    // ---------- Copy results back ----------
    cudaMemcpyAsync(h_out, d_out0, size_0 * sizeof(float),
                    cudaMemcpyDeviceToHost, stream0);

    // BUG 3: uses size_0 instead of size_1 for partition 1
    cudaMemcpyAsync(h_out + mid, d_out1, size_0 * sizeof(float),
                    cudaMemcpyDeviceToHost, stream1);

    cudaStreamSynchronize(stream0);
    cudaStreamSynchronize(stream1);

    cudaFree(d_in0);
    cudaFree(d_out0);
    cudaFree(d_in1);
    cudaFree(d_out1);
    cudaStreamDestroy(stream0);
    cudaStreamDestroy(stream1);
}

// ---------------------------------------------------------------------------
// Verification helpers
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

    float *h_in      = (float *)malloc(N * sizeof(float));
    float *cpu_out   = (float *)malloc(N * sizeof(float));
    float *gpu_out   = (float *)calloc(N, sizeof(float));
    if (!h_in || !cpu_out || !gpu_out) {
        fprintf(stderr, "ERROR: malloc\n");
        return 1;
    }

    srand(seed);
    for (int i = 0; i < N; i++) {
        h_in[i] = (float)(rand() % 1000) / 10.0f;
    }

    cpu_square(h_in, cpu_out, N);
    gpu_square_multistream(h_in, gpu_out, N);

    int mismatches = 0;
    int first_bad = -1;
    int duplicates = 0;
    int garbage = 0;

    for (int i = 0; i < N; i++) {
        float diff = fabsf(cpu_out[i] - gpu_out[i]);
        if (diff > 0.01f) {
            if (first_bad < 0) first_bad = i;
            mismatches++;
            // Check for duplicates: value matches a neighbor's expected value
            if (i > 0 && fabsf(gpu_out[i] - cpu_out[i - 1]) < 0.01f) {
                duplicates++;
            }
            // Check for garbage: unreasonably large
            if (fabsf(gpu_out[i]) > 1e10f || gpu_out[i] < -1.0f) {
                garbage++;
            }
        }
    }

    int match = (mismatches == 0) ? 1 : 0;

    printf("SIZE=%d\n", N);
    printf("MISMATCHES=%d\n", mismatches);
    printf("DUPLICATES=%d\n", duplicates);
    printf("GARBAGE=%d\n", garbage);
    if (first_bad >= 0) {
        printf("FIRST_BAD_INDEX=%d\n", first_bad);
        printf("EXPECTED=%.4f\n", cpu_out[first_bad]);
        printf("GOT=%.4f\n", gpu_out[first_bad]);
    }
    printf("MATCH=%d\n", match);

    free(h_in);
    free(cpu_out);
    free(gpu_out);
    return match ? 0 : 1;
}
