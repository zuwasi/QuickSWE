#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define BLOCK_SIZE 256

// ---------------------------------------------------------------------------
// CPU reference 1D convolution (DO NOT MODIFY)
// ---------------------------------------------------------------------------
void cpu_convolve(const float *in, float *out, const float *filter,
                  int N, int filter_size) {
    int radius = filter_size / 2;
    for (int i = 0; i < N; i++) {
        float sum = 0.0f;
        for (int j = 0; j < filter_size; j++) {
            int idx = i - radius + j;
            float val = (idx >= 0 && idx < N) ? in[idx] : 0.0f;
            sum += val * filter[j];
        }
        out[i] = sum;
    }
}

// ---------------------------------------------------------------------------
// Naive CUDA convolution kernel (DO NOT MODIFY)
// ---------------------------------------------------------------------------
__global__ void naive_convolve_kernel(const float *in, float *out,
                                       const float *filter, int N,
                                       int filter_size) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= N) return;

    int radius = filter_size / 2;
    float sum = 0.0f;
    for (int j = 0; j < filter_size; j++) {
        int idx = i - radius + j;
        float val = (idx >= 0 && idx < N) ? in[idx] : 0.0f;
        sum += val * filter[j];
    }
    out[i] = sum;
}

void gpu_naive_convolve(const float *h_in, float *h_out,
                        const float *h_filter, int N, int filter_size) {
    float *d_in, *d_out, *d_filter;
    cudaMalloc(&d_in, N * sizeof(float));
    cudaMalloc(&d_out, N * sizeof(float));
    cudaMalloc(&d_filter, filter_size * sizeof(float));

    cudaMemcpy(d_in, h_in, N * sizeof(float), cudaMemcpyHostToDevice);
    cudaMemcpy(d_filter, h_filter, filter_size * sizeof(float), cudaMemcpyHostToDevice);

    int grid = (N + BLOCK_SIZE - 1) / BLOCK_SIZE;
    naive_convolve_kernel<<<grid, BLOCK_SIZE>>>(d_in, d_out, d_filter, N, filter_size);
    cudaDeviceSynchronize();

    cudaMemcpy(h_out, d_out, N * sizeof(float), cudaMemcpyDeviceToHost);
    cudaFree(d_in);
    cudaFree(d_out);
    cudaFree(d_filter);
}

// ---------------------------------------------------------------------------
// Tiled CUDA convolution kernel — STUB (to be implemented)
// ---------------------------------------------------------------------------
__global__ void tiled_convolve_kernel(const float *in, float *out,
                                       const float *filter, int N,
                                       int filter_size) {
    // TODO: implement tiled 1D convolution with shared memory and halo cells
    // 1. Determine tile start position and radius.
    // 2. Allocate shared memory for tile + 2*radius elements.
    // 3. Load tile data + left/right halo into shared memory.
    //    - Zero-pad for out-of-bounds accesses.
    // 4. __syncthreads()
    // 5. Compute convolution for this thread's output element using shared mem.
}

void gpu_tiled_convolve(const float *h_in, float *h_out,
                        const float *h_filter, int N, int filter_size) {
    // TODO: allocate device memory, launch tiled_convolve_kernel, copy back
    // For now, just zero the output
    memset(h_out, 0, N * sizeof(float));
}

// ---------------------------------------------------------------------------
int main(int argc, char **argv) {
    int N = 256;
    int filter_size = 3;
    unsigned int seed = 42;
    const char *mode = "tiled";  // "naive" or "tiled"

    for (int k = 1; k < argc; k++) {
        if (strcmp(argv[k], "--size") == 0 && k + 1 < argc) {
            N = atoi(argv[++k]);
        } else if (strcmp(argv[k], "--filter") == 0 && k + 1 < argc) {
            filter_size = atoi(argv[++k]);
        } else if (strcmp(argv[k], "--seed") == 0 && k + 1 < argc) {
            seed = (unsigned int)atoi(argv[++k]);
        } else if (strcmp(argv[k], "--mode") == 0 && k + 1 < argc) {
            mode = argv[++k];
        }
    }

    // Force odd filter size
    if (filter_size % 2 == 0) filter_size++;

    float *in      = (float *)malloc(N * sizeof(float));
    float *filter  = (float *)malloc(filter_size * sizeof(float));
    float *cpu_out = (float *)malloc(N * sizeof(float));
    float *gpu_out = (float *)malloc(N * sizeof(float));
    if (!in || !filter || !cpu_out || !gpu_out) {
        fprintf(stderr, "ERROR: malloc\n");
        return 1;
    }

    srand(seed);
    for (int i = 0; i < N; i++) {
        in[i] = (float)(rand() % 1000) / 100.0f;
    }

    // Normalised filter
    float fsum = 0.0f;
    for (int j = 0; j < filter_size; j++) {
        filter[j] = (float)(rand() % 100 + 1);
        fsum += filter[j];
    }
    for (int j = 0; j < filter_size; j++) {
        filter[j] /= fsum;
    }

    // CPU reference
    cpu_convolve(in, cpu_out, filter, N, filter_size);

    // GPU
    if (strcmp(mode, "naive") == 0) {
        gpu_naive_convolve(in, gpu_out, filter, N, filter_size);
    } else {
        gpu_tiled_convolve(in, gpu_out, filter, N, filter_size);
    }

    // Compare
    int mismatches = 0;
    float max_rel_err = 0.0f;
    for (int i = 0; i < N; i++) {
        float diff = fabsf(cpu_out[i] - gpu_out[i]);
        float ref = fabsf(cpu_out[i]);
        float rel = (ref > 1e-8f) ? diff / ref : diff;
        if (rel > max_rel_err) max_rel_err = rel;
        if (rel > 1e-5f) mismatches++;
    }

    printf("SIZE=%d\n", N);
    printf("FILTER_SIZE=%d\n", filter_size);
    printf("MODE=%s\n", mode);
    printf("MISMATCHES=%d\n", mismatches);
    printf("MAX_REL_ERR=%.8f\n", max_rel_err);
    printf("MATCH=%d\n", mismatches == 0 ? 1 : 0);

    free(in);
    free(filter);
    free(cpu_out);
    free(gpu_out);
    return mismatches == 0 ? 0 : 1;
}
