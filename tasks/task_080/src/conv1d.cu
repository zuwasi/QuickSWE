#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define BLOCK_SIZE 128
#define MAX_RADIUS 16

/* ------------------------------------------------------------------ */
/* CPU reference (DO NOT MODIFY)                                      */
/* ------------------------------------------------------------------ */
void cpu_conv1d(const float *in, const float *kernel_w, float *out,
                int N, int ksize) {
    int radius = ksize / 2;
    for (int i = 0; i < N; i++) {
        float sum = 0.0f;
        for (int j = -radius; j <= radius; j++) {
            int idx = i + j;
            float val = (idx >= 0 && idx < N) ? in[idx] : 0.0f;
            sum += val * kernel_w[j + radius];
        }
        out[i] = sum;
    }
}

/* ------------------------------------------------------------------ */
/* GPU kernel                                                          */
/* ------------------------------------------------------------------ */
__global__ void conv1d_kernel(const float *in, const float *kernel_w,
                               float *out, int N, int radius) {
    extern __shared__ float smem[];

    int gid = blockIdx.x * blockDim.x + threadIdx.x;
    int lid = threadIdx.x;
    int tile_width = blockDim.x + 2 * radius;

    /* Load center elements */
    if (gid < N) {
        smem[lid + radius] = in[gid];
    } else {
        smem[lid + radius] = 0.0f;
    }

    /* Load left halo */
    if (lid < radius) {
        int halo_idx = gid - radius + lid;
        if (halo_idx >= 0) {
            smem[lid] = in[halo_idx];
        } else {
            smem[lid] = 0.0f;
        }
    }

    /* Load right halo */
    if (lid >= blockDim.x - radius) {
        int halo_idx = gid + radius;
        if (halo_idx < N) {
            smem[lid + 2 * radius] = in[halo_idx];
        } else {
            smem[lid + 2 * radius] = 0.0f;
        }
    }

    __syncthreads();

    /* Compute convolution */
    if (gid < N) {
        float sum = 0.0f;
        for (int j = -radius; j <= radius; j++) {
            sum += smem[lid + radius + j] * kernel_w[j + radius];
        }
        out[gid] = sum;
    }
}

/* ------------------------------------------------------------------ */
/* GPU driver                                                          */
/* ------------------------------------------------------------------ */
void gpu_conv1d(const float *h_in, const float *h_kw, float *h_out,
                int N, int ksize) {
    int radius = ksize / 2;
    float *d_in, *d_kw, *d_out;

    cudaMalloc(&d_in,  N * sizeof(float));
    cudaMalloc(&d_kw,  ksize * sizeof(float));
    cudaMalloc(&d_out, N * sizeof(float));

    cudaMemcpy(d_in, h_in, N * sizeof(float), cudaMemcpyHostToDevice);
    cudaMemcpy(d_kw, h_kw, ksize * sizeof(float), cudaMemcpyHostToDevice);
    cudaMemset(d_out, 0, N * sizeof(float));

    int grid = (N + BLOCK_SIZE - 1) / BLOCK_SIZE;
    int smem_sz = (BLOCK_SIZE + 2 * radius) * sizeof(float);

    conv1d_kernel<<<grid, BLOCK_SIZE, smem_sz>>>(d_in, d_kw, d_out, N, radius);
    cudaDeviceSynchronize();

    cudaMemcpy(h_out, d_out, N * sizeof(float), cudaMemcpyDeviceToHost);

    cudaFree(d_in);
    cudaFree(d_kw);
    cudaFree(d_out);
}

/* ------------------------------------------------------------------ */
void fill_array(float *arr, int N, unsigned int seed) {
    for (int i = 0; i < N; i++) {
        seed = seed * 1103515245u + 12345u;
        arr[i] = (float)(seed % 1000) / 100.0f;
    }
}

void make_kernel(float *kw, int ksize) {
    /* Simple averaging kernel */
    float val = 1.0f / (float)ksize;
    for (int i = 0; i < ksize; i++) kw[i] = val;
}

int main(int argc, char **argv) {
    int N = 500;
    int ksize = 5;
    unsigned int seed = 42;

    for (int k = 1; k < argc; k++) {
        if (strcmp(argv[k], "--size") == 0 && k+1 < argc) N = atoi(argv[++k]);
        else if (strcmp(argv[k], "--ksize") == 0 && k+1 < argc) ksize = atoi(argv[++k]);
        else if (strcmp(argv[k], "--seed") == 0 && k+1 < argc) seed = (unsigned int)atoi(argv[++k]);
    }
    if (ksize % 2 == 0) ksize++;
    if (ksize / 2 > MAX_RADIUS) ksize = 2 * MAX_RADIUS + 1;

    float *in      = (float *)malloc(N * sizeof(float));
    float *kw      = (float *)malloc(ksize * sizeof(float));
    float *cpu_out = (float *)malloc(N * sizeof(float));
    float *gpu_out = (float *)malloc(N * sizeof(float));

    fill_array(in, N, seed);
    make_kernel(kw, ksize);

    cpu_conv1d(in, kw, cpu_out, N, ksize);
    gpu_conv1d(in, kw, gpu_out, N, ksize);

    int mismatches = 0;
    float max_err = 0.0f;
    int boundary_errors = 0;
    int radius = ksize / 2;
    for (int i = 0; i < N; i++) {
        float err = fabsf(cpu_out[i] - gpu_out[i]);
        if (err > max_err) max_err = err;
        if (err > 0.01f) {
            mismatches++;
            if (i < radius || i >= N - radius) boundary_errors++;
        }
    }

    printf("N=%d\n", N);
    printf("KSIZE=%d\n", ksize);
    printf("MISMATCHES=%d\n", mismatches);
    printf("BOUNDARY_ERRORS=%d\n", boundary_errors);
    printf("MAX_ERROR=%.6e\n", max_err);
    printf("MATCH=%d\n", mismatches == 0 ? 1 : 0);

    free(in); free(kw); free(cpu_out); free(gpu_out);
    return mismatches == 0 ? 0 : 1;
}
