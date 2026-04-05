#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define BLOCK_SIZE 256
#define WARP_SIZE 32

/* ------------------------------------------------------------------ */
/* CPU reference (DO NOT MODIFY)                                      */
/* ------------------------------------------------------------------ */
void cpu_predicated_transform(const float *in, float *out, int N,
                               float threshold) {
    for (int base = 0; base < N; base += WARP_SIZE) {
        float warp_sum_above = 0.0f;
        float warp_sum_below = 0.0f;
        int count_above = 0, count_below = 0;

        int warp_end = base + WARP_SIZE;
        if (warp_end > N) warp_end = N;

        for (int i = base; i < warp_end; i++) {
            if (in[i] > threshold) {
                warp_sum_above += in[i];
                count_above++;
            } else {
                warp_sum_below += in[i];
                count_below++;
            }
        }

        float avg_above = (count_above > 0) ? warp_sum_above / count_above : 0.0f;
        float avg_below = (count_below > 0) ? warp_sum_below / count_below : 0.0f;

        for (int i = base; i < warp_end; i++) {
            if (in[i] > threshold) {
                out[i] = in[i] - avg_above;
            } else {
                out[i] = in[i] + avg_below;
            }
        }
    }
}

/* ------------------------------------------------------------------ */
/* GPU kernel                                                          */
/* ------------------------------------------------------------------ */
__global__ void predicated_transform_kernel(const float *in, float *out,
                                              int N, float threshold) {
    int gid = blockIdx.x * blockDim.x + threadIdx.x;
    if (gid >= N) return;

    float val = in[gid];
    int pred = (val > threshold) ? 1 : 0;

    unsigned int mask_above = __ballot_sync(0x0000FFFF, pred);
    unsigned int mask_below = __ballot_sync(0x0000FFFF, !pred);

    int lane = threadIdx.x % WARP_SIZE;

    /* Sum values for threads above threshold */
    float sum_above = 0.0f;
    for (int offset = WARP_SIZE / 2; offset > 0; offset /= 2) {
        float other = __shfl_down_sync(0xFFFFFFFF, pred ? val : 0.0f, offset);
        sum_above += other;
    }
    sum_above += pred ? val : 0.0f;
    sum_above = __shfl_sync(0xFFFFFFFF, sum_above, 0);
    int count_above = __popc(mask_above);

    /* Sum values for threads below threshold */
    float sum_below = 0.0f;
    for (int offset = WARP_SIZE / 2; offset > 0; offset /= 2) {
        float other = __shfl_down_sync(0xFFFFFFFF, pred ? 0.0f : val, offset);
        sum_below += other;
    }
    sum_below += pred ? 0.0f : val;
    sum_below = __shfl_sync(0xFFFFFFFF, sum_below, 0);
    int count_below = __popc(mask_below);

    float avg_above = (count_above > 0) ? sum_above / count_above : 0.0f;
    float avg_below = (count_below > 0) ? sum_below / count_below : 0.0f;

    if (pred) {
        out[gid] = val - avg_above;
    } else {
        out[gid] = val + avg_below;
    }
}

/* ------------------------------------------------------------------ */
void gpu_predicated_transform(const float *h_in, float *h_out, int N,
                               float threshold) {
    float *d_in, *d_out;
    cudaMalloc(&d_in,  N * sizeof(float));
    cudaMalloc(&d_out, N * sizeof(float));
    cudaMemcpy(d_in, h_in, N * sizeof(float), cudaMemcpyHostToDevice);

    int grid = (N + BLOCK_SIZE - 1) / BLOCK_SIZE;
    predicated_transform_kernel<<<grid, BLOCK_SIZE>>>(d_in, d_out, N, threshold);
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
    int N = 1024;
    float threshold = 50.0f;
    unsigned int seed = 42;

    for (int k = 1; k < argc; k++) {
        if (strcmp(argv[k], "--size") == 0 && k+1 < argc) N = atoi(argv[++k]);
        else if (strcmp(argv[k], "--threshold") == 0 && k+1 < argc) threshold = atof(argv[++k]);
        else if (strcmp(argv[k], "--seed") == 0 && k+1 < argc) seed = (unsigned int)atoi(argv[++k]);
    }

    float *in      = (float *)malloc(N * sizeof(float));
    float *cpu_out = (float *)malloc(N * sizeof(float));
    float *gpu_out = (float *)malloc(N * sizeof(float));

    fill_array(in, N, seed);
    cpu_predicated_transform(in, cpu_out, N, threshold);
    gpu_predicated_transform(in, gpu_out, N, threshold);

    int mismatches = 0;
    float max_err = 0.0f;
    for (int i = 0; i < N; i++) {
        float err = fabsf(cpu_out[i] - gpu_out[i]);
        if (err > max_err) max_err = err;
        if (err > 0.1f) mismatches++;
    }

    printf("N=%d\n", N);
    printf("THRESHOLD=%.1f\n", threshold);
    printf("MISMATCHES=%d\n", mismatches);
    printf("MAX_ERROR=%.6e\n", max_err);
    printf("MATCH=%d\n", mismatches == 0 ? 1 : 0);

    free(in); free(cpu_out); free(gpu_out);
    return mismatches == 0 ? 0 : 1;
}
