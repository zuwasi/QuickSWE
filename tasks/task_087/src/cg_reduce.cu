#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <cooperative_groups.h>
namespace cg = cooperative_groups;

#define BLOCK_SIZE 256

/* ------------------------------------------------------------------ */
/* CPU reference (DO NOT MODIFY)                                      */
/* ------------------------------------------------------------------ */
double cpu_reduce(const float *data, int N) {
    double sum = 0.0;
    for (int i = 0; i < N; i++) sum += (double)data[i];
    return sum;
}

/* ------------------------------------------------------------------ */
/* GPU kernel using cooperative groups                                  */
/* ------------------------------------------------------------------ */
template<int TILE_SZ>
__global__ void cg_reduce_kernel(const float *data, float *partial,
                                  int N) {
    __shared__ float sdata[BLOCK_SIZE];

    cg::thread_block block = cg::this_thread_block();
    int gid = blockIdx.x * blockDim.x + threadIdx.x;

    float val = (gid < N) ? data[gid] : 0.0f;

    /* Tile-level reduction */
    auto tile = cg::tiled_partition<TILE_SZ>(block);

    for (int offset = 32 / 2; offset > 0; offset /= 2) {
        val += tile.shfl_down(val, offset);
    }

    /* First thread of each tile writes to shared memory */
    int lane = threadIdx.x % 32;
    int tile_id = threadIdx.x / TILE_SZ;

    if (lane == 0) {
        sdata[tile_id] = val;
    }
    block.sync();

    /* First warp reduces tile results */
    int num_tiles = blockDim.x / TILE_SZ;
    if (threadIdx.x < num_tiles) {
        val = sdata[threadIdx.x];
    } else {
        val = 0.0f;
    }

    if (threadIdx.x < 32) {
        for (int offset = 16; offset > 0; offset /= 2) {
            val += __shfl_down_sync(0xFFFFFFFF, val, offset);
        }
    }

    if (threadIdx.x == 0) {
        partial[blockIdx.x] = val;
    }
}

/* ------------------------------------------------------------------ */
/* GPU driver                                                          */
/* ------------------------------------------------------------------ */
double gpu_reduce(const float *h_data, int N, int tile_size) {
    float *d_data;
    cudaMalloc(&d_data, N * sizeof(float));
    cudaMemcpy(d_data, h_data, N * sizeof(float), cudaMemcpyHostToDevice);

    int num_blocks = (N + BLOCK_SIZE - 1) / BLOCK_SIZE;
    float *d_partial;
    cudaMalloc(&d_partial, num_blocks * sizeof(float));

    switch (tile_size) {
        case 4:
            cg_reduce_kernel<4><<<num_blocks, BLOCK_SIZE>>>(d_data, d_partial, N);
            break;
        case 8:
            cg_reduce_kernel<8><<<num_blocks, BLOCK_SIZE>>>(d_data, d_partial, N);
            break;
        case 16:
            cg_reduce_kernel<16><<<num_blocks, BLOCK_SIZE>>>(d_data, d_partial, N);
            break;
        case 32:
        default:
            cg_reduce_kernel<32><<<num_blocks, BLOCK_SIZE>>>(d_data, d_partial, N);
            break;
    }
    cudaDeviceSynchronize();

    float *h_partial = (float *)malloc(num_blocks * sizeof(float));
    cudaMemcpy(h_partial, d_partial, num_blocks * sizeof(float),
               cudaMemcpyDeviceToHost);

    double total = 0.0;
    for (int i = 0; i < num_blocks; i++) total += (double)h_partial[i];

    cudaFree(d_data); cudaFree(d_partial); free(h_partial);
    return total;
}

/* ------------------------------------------------------------------ */
void fill_array(float *arr, int N, unsigned int seed) {
    for (int i = 0; i < N; i++) {
        seed = seed * 1103515245u + 12345u;
        arr[i] = (float)(seed % 1000) / 100.0f;
    }
}

int main(int argc, char **argv) {
    int N = 5000;
    int tile_size = 16;
    unsigned int seed = 42;

    for (int k = 1; k < argc; k++) {
        if (strcmp(argv[k], "--size") == 0 && k+1 < argc) N = atoi(argv[++k]);
        else if (strcmp(argv[k], "--tile") == 0 && k+1 < argc) tile_size = atoi(argv[++k]);
        else if (strcmp(argv[k], "--seed") == 0 && k+1 < argc) seed = (unsigned int)atoi(argv[++k]);
    }

    float *data = (float *)malloc(N * sizeof(float));
    fill_array(data, N, seed);

    double cpu_sum = cpu_reduce(data, N);
    double gpu_sum = gpu_reduce(data, N, tile_size);

    double rel_err = fabs(cpu_sum - gpu_sum) / fabs(cpu_sum + 1e-12);

    printf("N=%d\n", N);
    printf("TILE_SIZE=%d\n", tile_size);
    printf("CPU_SUM=%.6f\n", cpu_sum);
    printf("GPU_SUM=%.6f\n", gpu_sum);
    printf("REL_ERROR=%.6e\n", rel_err);
    printf("MATCH=%d\n", rel_err < 1e-3 ? 1 : 0);

    free(data);
    return rel_err < 1e-3 ? 0 : 1;
}
