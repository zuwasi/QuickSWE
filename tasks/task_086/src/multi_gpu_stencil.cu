#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define BLOCK_SIZE 256
#define STENCIL_RADIUS 2

/* ------------------------------------------------------------------ */
/* CPU reference — 1D stencil average (DO NOT MODIFY)                 */
/* ------------------------------------------------------------------ */
void cpu_stencil(const float *in, float *out, int N) {
    for (int i = 0; i < N; i++) {
        float sum = 0.0f;
        int count = 0;
        for (int j = -STENCIL_RADIUS; j <= STENCIL_RADIUS; j++) {
            int idx = i + j;
            if (idx >= 0 && idx < N) {
                sum += in[idx];
                count++;
            }
        }
        out[i] = sum / (float)count;
    }
}

/* ------------------------------------------------------------------ */
/* GPU kernel — stencil on a partition with halo                       */
/* ------------------------------------------------------------------ */
__global__ void stencil_kernel(const float *in, float *out,
                                int part_size, int halo, int global_offset,
                                int total_N) {
    int lid = blockIdx.x * blockDim.x + threadIdx.x;
    int gid = global_offset + lid;

    if (lid >= part_size || gid >= total_N) return;

    float sum = 0.0f;
    int count = 0;
    for (int j = -STENCIL_RADIUS; j <= STENCIL_RADIUS; j++) {
        int local_idx = lid + halo + j;
        int global_idx = gid + j;
        if (global_idx >= 0 && global_idx < total_N && local_idx >= 0) {
            sum += in[local_idx];
            count++;
        }
    }
    out[lid] = sum / (float)count;
}

/* ------------------------------------------------------------------ */
/* GPU driver — multi-partition with stream-based concurrency          */
/* ------------------------------------------------------------------ */
void gpu_stencil_multi(const float *h_in, float *h_out, int N,
                        int num_partitions) {
    int part_size = (N + num_partitions - 1) / num_partitions;

    cudaStream_t *streams = (cudaStream_t *)malloc(num_partitions * sizeof(cudaStream_t));
    float **d_in_parts  = (float **)malloc(num_partitions * sizeof(float *));
    float **d_out_parts = (float **)malloc(num_partitions * sizeof(float *));

    for (int p = 0; p < num_partitions; p++) {
        cudaStreamCreate(&streams[p]);

        int start = p * part_size;
        int end = start + part_size;
        if (end > N) end = N;
        int psize = end - start;

        int halo_left  = (start > STENCIL_RADIUS) ? STENCIL_RADIUS : start;
        int halo_right = (end + STENCIL_RADIUS <= N) ? STENCIL_RADIUS : (N - end);
        int alloc_size = halo_left + psize + halo_right;

        cudaMalloc(&d_in_parts[p], alloc_size * sizeof(float));
        cudaMalloc(&d_out_parts[p], psize * sizeof(float));

        /* Copy input with halos — uses default stream instead of partition stream */
        cudaMemcpy(d_in_parts[p], h_in + start - halo_left,
                   alloc_size * sizeof(float), cudaMemcpyHostToDevice);

        int grid = (psize + BLOCK_SIZE - 1) / BLOCK_SIZE;
        stencil_kernel<<<grid, BLOCK_SIZE, 0, streams[p]>>>(
            d_in_parts[p], d_out_parts[p], psize, halo_left, start, N);
    }

    /* Copy results back — doesn't synchronize streams first */
    for (int p = 0; p < num_partitions; p++) {
        int start = p * part_size;
        int end = start + part_size;
        if (end > N) end = N;
        int psize = end - start;

        cudaMemcpy(h_out + start, d_out_parts[p],
                   psize * sizeof(float), cudaMemcpyDeviceToHost);

        cudaFree(d_in_parts[p]);
        cudaFree(d_out_parts[p]);
        cudaStreamDestroy(streams[p]);
    }

    free(streams);
    free(d_in_parts);
    free(d_out_parts);
}

/* Single-partition reference */
void gpu_stencil_single(const float *h_in, float *h_out, int N) {
    float *d_in, *d_out;
    cudaMalloc(&d_in,  N * sizeof(float));
    cudaMalloc(&d_out, N * sizeof(float));
    cudaMemcpy(d_in, h_in, N * sizeof(float), cudaMemcpyHostToDevice);

    int grid = (N + BLOCK_SIZE - 1) / BLOCK_SIZE;
    stencil_kernel<<<grid, BLOCK_SIZE>>>(d_in, d_out, N, 0, 0, N);
    cudaDeviceSynchronize();

    cudaMemcpy(h_out, d_out, N * sizeof(float), cudaMemcpyDeviceToHost);
    cudaFree(d_in); cudaFree(d_out);
}

/* ------------------------------------------------------------------ */
void fill_array(float *arr, int N, unsigned int seed) {
    for (int i = 0; i < N; i++) {
        seed = seed * 1103515245u + 12345u;
        arr[i] = (float)(seed % 10000) / 100.0f;
    }
}

int main(int argc, char **argv) {
    int N = 2000;
    int parts = 4;
    unsigned int seed = 42;

    for (int k = 1; k < argc; k++) {
        if (strcmp(argv[k], "--size") == 0 && k+1 < argc) N = atoi(argv[++k]);
        else if (strcmp(argv[k], "--parts") == 0 && k+1 < argc) parts = atoi(argv[++k]);
        else if (strcmp(argv[k], "--seed") == 0 && k+1 < argc) seed = (unsigned int)atoi(argv[++k]);
    }

    float *in      = (float *)malloc(N * sizeof(float));
    float *cpu_out = (float *)malloc(N * sizeof(float));
    float *gpu_out = (float *)malloc(N * sizeof(float));

    fill_array(in, N, seed);
    cpu_stencil(in, cpu_out, N);
    gpu_stencil_multi(in, gpu_out, N, parts);

    int mismatches = 0;
    float max_err = 0.0f;
    int boundary_mismatches = 0;
    for (int i = 0; i < N; i++) {
        float err = fabsf(cpu_out[i] - gpu_out[i]);
        if (err > max_err) max_err = err;
        if (err > 0.01f) {
            mismatches++;
            int part_size = (N + parts - 1) / parts;
            if (i % part_size < STENCIL_RADIUS || i % part_size >= part_size - STENCIL_RADIUS)
                boundary_mismatches++;
        }
    }

    printf("N=%d\n", N);
    printf("PARTITIONS=%d\n", parts);
    printf("MISMATCHES=%d\n", mismatches);
    printf("BOUNDARY_MISMATCHES=%d\n", boundary_mismatches);
    printf("MAX_ERROR=%.6e\n", max_err);
    printf("MATCH=%d\n", mismatches == 0 ? 1 : 0);

    free(in); free(cpu_out); free(gpu_out);
    return mismatches == 0 ? 0 : 1;
}
