#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define BLOCK_SIZE 256

/* ------------------------------------------------------------------ */
/* CPU reference — exclusive scan (DO NOT MODIFY)                     */
/* ------------------------------------------------------------------ */
void cpu_exclusive_scan(const float *in, float *out, int N) {
    out[0] = 0.0f;
    for (int i = 1; i < N; i++) {
        out[i] = out[i - 1] + in[i - 1];
    }
}

/* ------------------------------------------------------------------ */
/* GPU kernel — Blelloch exclusive scan (single block)                */
/* ------------------------------------------------------------------ */
__global__ void exclusive_scan_kernel(const float *in, float *out, int N) {
    extern __shared__ float temp[];

    int tid = threadIdx.x;

    if (tid < N) {
        temp[tid] = in[tid];
    } else {
        temp[tid] = 0.0f;
    }
    __syncthreads();

    /* Up-sweep (reduce) */
    for (int stride = 1; stride < BLOCK_SIZE; stride *= 2) {
        int idx = (tid + 1) * stride * 2 - 1;
        if (idx < BLOCK_SIZE) {
            temp[idx] += temp[idx - stride];
        }
        __syncthreads();
    }

    /* Down-sweep — should produce exclusive scan but has wrong
       initialization: does not clear the last element to 0 */
    if (tid == 0) {
        temp[BLOCK_SIZE - 1] = temp[BLOCK_SIZE - 1];
    }
    __syncthreads();

    for (int stride = BLOCK_SIZE / 2; stride >= 1; stride /= 2) {
        int idx = (tid + 1) * stride * 2 - 1;
        if (idx < BLOCK_SIZE) {
            float t = temp[idx - stride];
            temp[idx - stride] = temp[idx];
            temp[idx] += t;
        }
        __syncthreads();
    }

    if (tid < N) {
        out[tid] = temp[tid];
    }
}

/* ------------------------------------------------------------------ */
/* GPU driver                                                          */
/* ------------------------------------------------------------------ */
void gpu_exclusive_scan(const float *h_in, float *h_out, int N) {
    float *d_in, *d_out;

    cudaMalloc(&d_in,  N * sizeof(float));
    cudaMalloc(&d_out, N * sizeof(float));

    cudaMemcpy(d_in, h_in, N * sizeof(float), cudaMemcpyHostToDevice);
    cudaMemset(d_out, 0, N * sizeof(float));

    exclusive_scan_kernel<<<1, BLOCK_SIZE, BLOCK_SIZE * sizeof(float)>>>(
        d_in, d_out, N);
    cudaDeviceSynchronize();

    cudaMemcpy(h_out, d_out, N * sizeof(float), cudaMemcpyDeviceToHost);

    cudaFree(d_in);
    cudaFree(d_out);
}

/* ------------------------------------------------------------------ */
void fill_array(float *arr, int N, unsigned int seed) {
    for (int i = 0; i < N; i++) {
        seed = seed * 1103515245u + 12345u;
        arr[i] = (float)(seed % 100) / 10.0f;
    }
}

int main(int argc, char **argv) {
    int N = 128;
    unsigned int seed = 42;

    for (int k = 1; k < argc; k++) {
        if (strcmp(argv[k], "--size") == 0 && k+1 < argc) N = atoi(argv[++k]);
        else if (strcmp(argv[k], "--seed") == 0 && k+1 < argc) seed = (unsigned int)atoi(argv[++k]);
    }
    if (N > BLOCK_SIZE) N = BLOCK_SIZE;

    float *in      = (float *)malloc(N * sizeof(float));
    float *cpu_out = (float *)malloc(N * sizeof(float));
    float *gpu_out = (float *)malloc(N * sizeof(float));

    fill_array(in, N, seed);
    cpu_exclusive_scan(in, cpu_out, N);
    gpu_exclusive_scan(in, gpu_out, N);

    int mismatches = 0;
    float max_err = 0.0f;
    for (int i = 0; i < N; i++) {
        float err = fabsf(cpu_out[i] - gpu_out[i]);
        if (err > max_err) max_err = err;
        if (err > 0.01f) mismatches++;
    }

    float first_err = fabsf(gpu_out[0] - 0.0f);

    printf("N=%d\n", N);
    printf("MISMATCHES=%d\n", mismatches);
    printf("MAX_ERROR=%.6e\n", max_err);
    printf("FIRST_ELEMENT=%.4f\n", gpu_out[0]);
    printf("FIRST_OK=%d\n", first_err < 0.001f ? 1 : 0);
    printf("MATCH=%d\n", mismatches == 0 ? 1 : 0);

    free(in); free(cpu_out); free(gpu_out);
    return mismatches == 0 ? 0 : 1;
}
