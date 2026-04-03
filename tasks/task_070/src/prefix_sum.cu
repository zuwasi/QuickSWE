#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define BLOCK_SIZE 256

// ---------------------------------------------------------------------------
// CPU reference exclusive prefix sum (DO NOT MODIFY)
// ---------------------------------------------------------------------------
void cpu_exclusive_scan(const int *in, int *out, int N) {
    out[0] = 0;
    for (int i = 1; i < N; i++) {
        out[i] = out[i - 1] + in[i - 1];
    }
}

// ---------------------------------------------------------------------------
// CUDA Blelloch scan kernel — BUGGY
// ---------------------------------------------------------------------------
__global__ void blelloch_scan_kernel(int *data, int *block_sums, int N) {
    __shared__ int temp[2 * BLOCK_SIZE];

    int tid = threadIdx.x;
    int offset = blockIdx.x * (2 * BLOCK_SIZE);

    // Load input into shared memory
    temp[2 * tid]     = (offset + 2 * tid     < N) ? data[offset + 2 * tid]     : 0;
    temp[2 * tid + 1] = (offset + 2 * tid + 1 < N) ? data[offset + 2 * tid + 1] : 0;

    // --- Up-sweep (reduce) ---
    // BUG 1: stride condition is wrong — uses stride < BLOCK_SIZE instead of
    // stride <= BLOCK_SIZE.  When stride == BLOCK_SIZE the final reduction
    // step (combining the two halves of the block) is skipped.
    int n = 2 * BLOCK_SIZE;
    for (int stride = 1; stride < BLOCK_SIZE; stride *= 2) {
        __syncthreads();
        int idx = (tid + 1) * stride * 2 - 1;
        if (idx < n) {
            temp[idx] += temp[idx - stride];
        }
    }

    // Save block sum and clear last element
    if (tid == 0) {
        if (block_sums != NULL) {
            block_sums[blockIdx.x] = temp[n - 1];
        }
        temp[n - 1] = 0;
    }

    // --- Down-sweep ---
    for (int stride = BLOCK_SIZE; stride >= 1; stride /= 2) {
        __syncthreads();
        int idx = (tid + 1) * stride * 2 - 1;
        if (idx < n) {
            int t = temp[idx - stride];
            temp[idx - stride] = temp[idx];
            temp[idx] += t;
        }
    }

    __syncthreads();

    // Write results back
    if (offset + 2 * tid < N)
        data[offset + 2 * tid] = temp[2 * tid];
    if (offset + 2 * tid + 1 < N)
        data[offset + 2 * tid + 1] = temp[2 * tid + 1];
}

// BUG 2: This kernel should add scanned block offsets to each block's
// elements, but it is never called.
__global__ void add_block_offsets(int *data, const int *block_offsets, int N) {
    int idx = blockIdx.x * (2 * BLOCK_SIZE) + threadIdx.x;
    if (blockIdx.x > 0 && idx < N) {
        data[idx] += block_offsets[blockIdx.x];
    }
    int idx2 = idx + BLOCK_SIZE;
    if (blockIdx.x > 0 && idx2 < N) {
        data[idx2] += block_offsets[blockIdx.x];
    }
}

// ---------------------------------------------------------------------------
// GPU exclusive prefix sum — BUGGY (does not combine inter-block results)
// ---------------------------------------------------------------------------
void gpu_exclusive_scan(const int *h_in, int *h_out, int N) {
    int elements_per_block = 2 * BLOCK_SIZE;
    int num_blocks = (N + elements_per_block - 1) / elements_per_block;

    int *d_data, *d_block_sums;
    cudaMalloc(&d_data, N * sizeof(int));
    cudaMalloc(&d_block_sums, num_blocks * sizeof(int));

    cudaMemcpy(d_data, h_in, N * sizeof(int), cudaMemcpyHostToDevice);

    // Run per-block scan
    blelloch_scan_kernel<<<num_blocks, BLOCK_SIZE>>>(d_data, d_block_sums, N);
    cudaDeviceSynchronize();

    // BUG 2: The block sums are computed but never scanned and never added
    // back to subsequent blocks.  For arrays that span multiple blocks the
    // result is wrong — each block's scan is independent.

    cudaMemcpy(h_out, d_data, N * sizeof(int), cudaMemcpyDeviceToHost);

    cudaFree(d_data);
    cudaFree(d_block_sums);
}

// ---------------------------------------------------------------------------
int main(int argc, char **argv) {
    int N = 128;
    unsigned int seed = 42;

    for (int k = 1; k < argc; k++) {
        if (strcmp(argv[k], "--size") == 0 && k + 1 < argc) {
            N = atoi(argv[++k]);
        } else if (strcmp(argv[k], "--seed") == 0 && k + 1 < argc) {
            seed = (unsigned int)atoi(argv[++k]);
        }
    }

    int *in      = (int *)malloc(N * sizeof(int));
    int *cpu_out = (int *)malloc(N * sizeof(int));
    int *gpu_out = (int *)malloc(N * sizeof(int));
    if (!in || !cpu_out || !gpu_out) {
        fprintf(stderr, "ERROR: malloc\n");
        return 1;
    }

    srand(seed);
    for (int i = 0; i < N; i++) {
        in[i] = rand() % 10;  // small values to avoid overflow
    }

    cpu_exclusive_scan(in, cpu_out, N);
    gpu_exclusive_scan(in, gpu_out, N);

    int mismatches = 0;
    int first_bad = -1;
    for (int i = 0; i < N; i++) {
        if (cpu_out[i] != gpu_out[i]) {
            if (first_bad < 0) first_bad = i;
            mismatches++;
        }
    }

    printf("SIZE=%d\n", N);
    printf("MISMATCHES=%d\n", mismatches);
    if (first_bad >= 0) {
        printf("FIRST_BAD_INDEX=%d\n", first_bad);
        printf("EXPECTED=%d\n", cpu_out[first_bad]);
        printf("GOT=%d\n", gpu_out[first_bad]);
    }
    printf("MATCH=%d\n", mismatches == 0 ? 1 : 0);

    free(in);
    free(cpu_out);
    free(gpu_out);
    return mismatches == 0 ? 0 : 1;
}
