#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define BLOCK_SIZE 256
#define RADIX_BITS 8
#define RADIX      (1 << RADIX_BITS)  // 256 buckets per pass
#define NUM_PASSES 4                  // 4 passes × 8 bits = 32 bits

// ---------------------------------------------------------------------------
// CPU reference sort (DO NOT MODIFY)
// ---------------------------------------------------------------------------
static int cmp_uint(const void *a, const void *b) {
    unsigned int ua = *(const unsigned int *)a;
    unsigned int ub = *(const unsigned int *)b;
    if (ua < ub) return -1;
    if (ua > ub) return  1;
    return 0;
}

void cpu_sort(const unsigned int *in, unsigned int *out, int N) {
    memcpy(out, in, N * sizeof(unsigned int));
    qsort(out, N, sizeof(unsigned int), cmp_uint);
}

// ---------------------------------------------------------------------------
// Histogram kernel — counts occurrences of each digit value
// ---------------------------------------------------------------------------
__global__ void histogram_kernel(const unsigned int *data, int *histogram,
                                 int N, int pass) {
    int tid = blockIdx.x * blockDim.x + threadIdx.x;

    __shared__ int local_hist[RADIX];
    if (threadIdx.x < RADIX) {
        local_hist[threadIdx.x] = 0;
    }
    __syncthreads();

    if (tid < N) {
        unsigned int val = data[tid];
        int digit = (val >> (pass * RADIX_BITS)) & (RADIX - 1);
        atomicAdd(&local_hist[digit], 1);
    }
    __syncthreads();

    if (threadIdx.x < RADIX) {
        atomicAdd(&histogram[threadIdx.x], local_hist[threadIdx.x]);
    }
}

// ---------------------------------------------------------------------------
// Prefix sum (exclusive scan) on histogram — CPU side for simplicity
// ---------------------------------------------------------------------------
void exclusive_prefix_sum(int *hist, int *prefix, int n) {
    prefix[0] = 0;
    for (int i = 1; i < n; i++) {
        prefix[i] = prefix[i - 1] + hist[i - 1];
    }
}

// ---------------------------------------------------------------------------
// Scatter kernel — places elements at their sorted positions   BUGGY
// ---------------------------------------------------------------------------

/*
 * BUG 1 — Wrong scatter offset:
 *   Each thread looks up prefix[digit] and does atomicAdd to get its
 *   output slot.  But the atomicAdd returns the OLD value before the
 *   add, so the first thread with a given digit goes to prefix[digit],
 *   the second goes to prefix[digit]+1, etc.  However, the kernel
 *   ALSO adds 'threadIdx.x' as a local offset, which double-counts
 *   the position.  This causes elements to be written to wrong (and
 *   sometimes out-of-bounds) locations, losing some values and
 *   duplicating others.
 *
 * BUG 2 — Inverted ping-pong on last pass:
 *   The host code alternates input/output buffers each pass.  On the
 *   LAST pass the swap is inverted: it reads from the wrong buffer
 *   and writes to the wrong one, so the final result is from the
 *   second-to-last pass (not fully sorted).
 */

__global__ void scatter_kernel(const unsigned int *in, unsigned int *out,
                               int *prefix, int N, int pass) {
    int tid = blockIdx.x * blockDim.x + threadIdx.x;
    if (tid < N) {
        unsigned int val = in[tid];
        int digit = (val >> (pass * RADIX_BITS)) & (RADIX - 1);

        // BUG 1: adds threadIdx.x as a local offset on top of atomicAdd
        int pos = atomicAdd(&prefix[digit], 1) + threadIdx.x;

        if (pos < N) {
            out[pos] = val;
        }
    }
}

// ---------------------------------------------------------------------------
// Host driver — BUGGY ping-pong logic
// ---------------------------------------------------------------------------
void gpu_radix_sort(const unsigned int *h_in, unsigned int *h_out, int N) {
    unsigned int *d_buf0, *d_buf1;
    int *d_histogram, *d_prefix;

    cudaMalloc(&d_buf0, N * sizeof(unsigned int));
    cudaMalloc(&d_buf1, N * sizeof(unsigned int));
    cudaMalloc(&d_histogram, RADIX * sizeof(int));
    cudaMalloc(&d_prefix,    RADIX * sizeof(int));

    cudaMemcpy(d_buf0, h_in, N * sizeof(unsigned int), cudaMemcpyHostToDevice);

    int grid = (N + BLOCK_SIZE - 1) / BLOCK_SIZE;

    int *h_hist   = (int *)malloc(RADIX * sizeof(int));
    int *h_prefix = (int *)malloc(RADIX * sizeof(int));

    for (int pass = 0; pass < NUM_PASSES; pass++) {
        unsigned int *src, *dst;

        // BUG 2: on last pass (pass == 3) the buffers are swapped
        if (pass == NUM_PASSES - 1) {
            // Inverted: reads from dst-of-previous-pass and writes back
            src = (pass % 2 == 0) ? d_buf1 : d_buf0;
            dst = (pass % 2 == 0) ? d_buf0 : d_buf1;
        } else {
            src = (pass % 2 == 0) ? d_buf0 : d_buf1;
            dst = (pass % 2 == 0) ? d_buf1 : d_buf0;
        }

        // Clear histogram
        cudaMemset(d_histogram, 0, RADIX * sizeof(int));

        // Build histogram
        histogram_kernel<<<grid, BLOCK_SIZE>>>(src, d_histogram, N, pass);
        cudaDeviceSynchronize();

        // Download histogram, compute prefix sum, upload
        cudaMemcpy(h_hist, d_histogram, RADIX * sizeof(int),
                   cudaMemcpyDeviceToHost);
        exclusive_prefix_sum(h_hist, h_prefix, RADIX);
        cudaMemcpy(d_prefix, h_prefix, RADIX * sizeof(int),
                   cudaMemcpyHostToDevice);

        // Scatter
        scatter_kernel<<<grid, BLOCK_SIZE>>>(src, dst, d_prefix, N, pass);
        cudaDeviceSynchronize();
    }

    // After 4 passes the result should be in d_buf0 (even number of swaps)
    // but due to BUG 2, the last pass wrote to the wrong buffer.
    cudaMemcpy(h_out, d_buf0, N * sizeof(unsigned int), cudaMemcpyDeviceToHost);

    free(h_hist);
    free(h_prefix);
    cudaFree(d_buf0);
    cudaFree(d_buf1);
    cudaFree(d_histogram);
    cudaFree(d_prefix);
}

// ---------------------------------------------------------------------------
// Verification
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

    unsigned int *data    = (unsigned int *)malloc(N * sizeof(unsigned int));
    unsigned int *cpu_out = (unsigned int *)malloc(N * sizeof(unsigned int));
    unsigned int *gpu_out = (unsigned int *)calloc(N, sizeof(unsigned int));
    if (!data || !cpu_out || !gpu_out) {
        fprintf(stderr, "ERROR: malloc\n");
        return 1;
    }

    srand(seed);
    for (int i = 0; i < N; i++) {
        data[i] = (unsigned int)(rand() & 0x7FFFFFFF);
    }

    cpu_sort(data, cpu_out, N);
    gpu_radix_sort(data, gpu_out, N);

    int mismatches = 0;
    int first_bad = -1;
    int sorted = 1;
    int lost = 0;
    int duped = 0;

    for (int i = 0; i < N; i++) {
        if (cpu_out[i] != gpu_out[i]) {
            if (first_bad < 0) first_bad = i;
            mismatches++;
        }
    }

    for (int i = 1; i < N; i++) {
        if (gpu_out[i] < gpu_out[i - 1]) {
            sorted = 0;
            break;
        }
    }

    // Simple lost/dup check: compare sorted arrays as multisets
    // Both cpu_out and gpu_out should be sorted, so walk both
    {
        int ci = 0, gi = 0;
        while (ci < N && gi < N) {
            if (cpu_out[ci] == gpu_out[gi]) {
                ci++; gi++;
            } else if (cpu_out[ci] < gpu_out[gi]) {
                lost++; ci++;
            } else {
                duped++; gi++;
            }
        }
        lost += (N - ci);
        duped += (N - gi);
    }

    int match = (mismatches == 0 && sorted) ? 1 : 0;

    printf("SIZE=%d\n", N);
    printf("MISMATCHES=%d\n", mismatches);
    printf("SORTED=%d\n", sorted);
    printf("LOST=%d\n", lost);
    printf("DUPED=%d\n", duped);
    if (first_bad >= 0) {
        printf("FIRST_BAD_INDEX=%d\n", first_bad);
        printf("EXPECTED=%u\n", cpu_out[first_bad]);
        printf("GOT=%u\n", gpu_out[first_bad]);
    }
    printf("MATCH=%d\n", match);

    free(data);
    free(cpu_out);
    free(gpu_out);
    return match ? 0 : 1;
}
