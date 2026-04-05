#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define MAX_DEPTH 10

/* ------------------------------------------------------------------ */
/* CPU reference (DO NOT MODIFY)                                      */
/* ------------------------------------------------------------------ */
int cmp_float(const void *a, const void *b) {
    float fa = *(const float *)a, fb = *(const float *)b;
    return (fa > fb) - (fa < fb);
}
void cpu_sort(float *data, int N) {
    qsort(data, N, sizeof(float), cmp_float);
}

/* ------------------------------------------------------------------ */
/* Device merge function                                               */
/* ------------------------------------------------------------------ */
__device__ void device_merge(float *data, float *temp,
                              int left, int mid, int right) {
    int i = left, j = mid, k = left;
    while (i < mid && j < right) {
        if (data[i] <= data[j])
            temp[k++] = data[i++];
        else
            temp[k++] = data[j++];
    }
    while (i < mid) temp[k++] = data[i++];
    while (j < right) temp[k++] = data[j++];
    for (int x = left; x < right; x++) data[x] = temp[x];
}

/* ------------------------------------------------------------------ */
/* Simple insertion sort for base case                                 */
/* ------------------------------------------------------------------ */
__device__ void device_insertion_sort(float *data, int left, int right) {
    for (int i = left + 1; i < right; i++) {
        float key = data[i];
        int j = i - 1;
        while (j >= left && data[j] > key) {
            data[j + 1] = data[j];
            j--;
        }
        data[j + 1] = key;
    }
}

/* ------------------------------------------------------------------ */
/* Recursive merge sort kernel                                         */
/* ------------------------------------------------------------------ */
__global__ void mergesort_kernel(float *data, float *temp,
                                   int left, int right, int depth) {
    if (right - left <= 1) return;

    int mid = (left + right) / 2;

    if (depth >= MAX_DEPTH || right - left <= 1) {
        device_insertion_sort(data, left, right);
        return;
    }

    /* Launch child kernels on default stream (BUG: causes deadlock
       when multiple parents run concurrently) */
    mergesort_kernel<<<1, 1>>>(data, temp, left, mid, depth + 1);
    mergesort_kernel<<<1, 1>>>(data, temp, mid, right, depth + 1);

    /* Wait for children — uses cudaDeviceSynchronize which waits
       for ALL device work, not just our children */
    cudaDeviceSynchronize();

    device_merge(data, temp, left, mid, right);
}

/* ------------------------------------------------------------------ */
void gpu_sort(float *h_data, int N) {
    float *d_data, *d_temp;

    cudaMalloc(&d_data, N * sizeof(float));
    cudaMalloc(&d_temp, N * sizeof(float));
    cudaMemcpy(d_data, h_data, N * sizeof(float), cudaMemcpyHostToDevice);

    cudaDeviceSetLimit(cudaLimitDevRuntimeSyncDepth, MAX_DEPTH + 2);
    cudaDeviceSetLimit(cudaLimitDevRuntimePendingLaunchCount, 4096);

    mergesort_kernel<<<1, 1>>>(d_data, d_temp, 0, N, 0);

    cudaError_t err = cudaDeviceSynchronize();
    if (err != cudaSuccess) {
        fprintf(stderr, "GPU_ERROR=%d\n", (int)err);
    }

    cudaMemcpy(h_data, d_data, N * sizeof(float), cudaMemcpyDeviceToHost);
    cudaFree(d_data); cudaFree(d_temp);
}

/* ------------------------------------------------------------------ */
void fill_array(float *arr, int N, unsigned int seed) {
    for (int i = 0; i < N; i++) {
        seed = seed * 1103515245u + 12345u;
        arr[i] = (float)(seed % 100000) / 100.0f;
    }
}

int main(int argc, char **argv) {
    int N = 512;
    unsigned int seed = 42;

    for (int k = 1; k < argc; k++) {
        if (strcmp(argv[k], "--size") == 0 && k+1 < argc) N = atoi(argv[++k]);
        else if (strcmp(argv[k], "--seed") == 0 && k+1 < argc) seed = (unsigned int)atoi(argv[++k]);
    }

    float *cpu_data = (float *)malloc(N * sizeof(float));
    float *gpu_data = (float *)malloc(N * sizeof(float));

    fill_array(cpu_data, N, seed);
    memcpy(gpu_data, cpu_data, N * sizeof(float));

    cpu_sort(cpu_data, N);
    gpu_sort(gpu_data, N);

    int mismatches = 0;
    int sorted = 1;
    for (int i = 0; i < N; i++) {
        if (fabsf(cpu_data[i] - gpu_data[i]) > 1e-5f) mismatches++;
        if (i > 0 && gpu_data[i] < gpu_data[i - 1] - 1e-5f) sorted = 0;
    }

    printf("N=%d\n", N);
    printf("MISMATCHES=%d\n", mismatches);
    printf("SORTED=%d\n", sorted);
    printf("MATCH=%d\n", mismatches == 0 ? 1 : 0);

    free(cpu_data); free(gpu_data);
    return mismatches == 0 ? 0 : 1;
}
