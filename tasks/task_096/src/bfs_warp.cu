#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define BLOCK_SIZE 256
#define WARP_SIZE 32
#define MAX_FRONTIER 100000

/* ------------------------------------------------------------------ */
/* CPU BFS reference (DO NOT MODIFY)                                  */
/* ------------------------------------------------------------------ */
void cpu_bfs(const int *row_ptr, const int *col_idx, int *dist,
             int N, int source) {
    for (int i = 0; i < N; i++) dist[i] = -1;
    dist[source] = 0;

    int *queue = (int *)malloc(N * sizeof(int));
    int front = 0, back = 0;
    queue[back++] = source;

    while (front < back) {
        int v = queue[front++];
        for (int j = row_ptr[v]; j < row_ptr[v + 1]; j++) {
            int u = col_idx[j];
            if (dist[u] == -1) {
                dist[u] = dist[v] + 1;
                queue[back++] = u;
            }
        }
    }
    free(queue);
}

/* ------------------------------------------------------------------ */
/* GPU BFS kernel — warp-centric                                       */
/* ------------------------------------------------------------------ */
__global__ void bfs_kernel(const int *row_ptr, const int *col_idx,
                            int *dist, const int *frontier_in, int frontier_size,
                            int *frontier_out, int *out_size, int level) {
    int tid = blockIdx.x * blockDim.x + threadIdx.x;
    int warp_id = tid / WARP_SIZE;
    int lane = tid % WARP_SIZE;

    if (warp_id >= frontier_size) return;

    int v = frontier_in[warp_id];
    int start = row_ptr[v];
    int end = row_ptr[v + 1];
    int degree = end - start;

    /* Each lane processes a subset of neighbors */
    for (int i = lane; i < degree; i += WARP_SIZE) {
        int u = col_idx[start + i];

        /* Non-atomic check — race condition: multiple warps may both
           see dist[u] == -1 and both add u to frontier */
        if (dist[u] == -1) {
            dist[u] = level + 1;

            /* Non-atomic frontier append — race condition */
            int pos = *out_size;
            *out_size = pos + 1;
            if (pos < MAX_FRONTIER) {
                frontier_out[pos] = u;
            }
        }
    }
}

/* ------------------------------------------------------------------ */
void gpu_bfs(const int *h_row_ptr, const int *h_col_idx, int *h_dist,
             int N, int nnz, int source) {
    int *d_row_ptr, *d_col_idx, *d_dist;
    int *d_frontier_in, *d_frontier_out, *d_out_size;

    cudaMalloc(&d_row_ptr, (N + 1) * sizeof(int));
    cudaMalloc(&d_col_idx, nnz * sizeof(int));
    cudaMalloc(&d_dist, N * sizeof(int));
    cudaMalloc(&d_frontier_in, MAX_FRONTIER * sizeof(int));
    cudaMalloc(&d_frontier_out, MAX_FRONTIER * sizeof(int));
    cudaMalloc(&d_out_size, sizeof(int));

    cudaMemcpy(d_row_ptr, h_row_ptr, (N + 1) * sizeof(int), cudaMemcpyHostToDevice);
    cudaMemcpy(d_col_idx, h_col_idx, nnz * sizeof(int), cudaMemcpyHostToDevice);

    /* Initialize distances to -1, source to 0 */
    cudaMemset(d_dist, 0xFF, N * sizeof(int));  /* -1 in two's complement */
    int zero = 0;
    cudaMemcpy(d_dist + source, &zero, sizeof(int), cudaMemcpyHostToDevice);

    /* Initial frontier = {source} */
    cudaMemcpy(d_frontier_in, &source, sizeof(int), cudaMemcpyHostToDevice);
    int frontier_size = 1;

    for (int level = 0; frontier_size > 0 && level < N; level++) {
        cudaMemset(d_out_size, 0, sizeof(int));

        int num_warps = frontier_size;
        int num_threads = num_warps * WARP_SIZE;
        int grid = (num_threads + BLOCK_SIZE - 1) / BLOCK_SIZE;

        bfs_kernel<<<grid, BLOCK_SIZE>>>(d_row_ptr, d_col_idx, d_dist,
            d_frontier_in, frontier_size,
            d_frontier_out, d_out_size, level);
        cudaDeviceSynchronize();

        cudaMemcpy(&frontier_size, d_out_size, sizeof(int), cudaMemcpyDeviceToHost);
        if (frontier_size > MAX_FRONTIER) frontier_size = MAX_FRONTIER;

        /* Swap frontier buffers */
        int *tmp = d_frontier_in;
        d_frontier_in = d_frontier_out;
        d_frontier_out = tmp;
    }

    cudaMemcpy(h_dist, d_dist, N * sizeof(int), cudaMemcpyDeviceToHost);

    cudaFree(d_row_ptr); cudaFree(d_col_idx); cudaFree(d_dist);
    cudaFree(d_frontier_in); cudaFree(d_frontier_out); cudaFree(d_out_size);
}

/* ------------------------------------------------------------------ */
/* Generate a random connected graph in CSR format                     */
/* ------------------------------------------------------------------ */
void generate_graph(int N, int avg_degree, unsigned int seed,
                    int **row_ptr, int **col_idx, int *nnz_out) {
    *row_ptr = (int *)malloc((N + 1) * sizeof(int));

    /* First pass: count edges */
    int nnz = 0;
    (*row_ptr)[0] = 0;
    for (int i = 0; i < N; i++) {
        seed = seed * 1103515245u + 12345u;
        int deg = 1 + (seed % (2 * avg_degree));
        nnz += deg;
        (*row_ptr)[i + 1] = nnz;
    }
    /* Ensure connectivity: add edge to next vertex */
    nnz += N - 1;

    *col_idx = (int *)malloc(nnz * sizeof(int));

    /* Second pass: fill edges */
    int edge_idx = 0;
    for (int i = 0; i < N; i++) {
        int start = (*row_ptr)[i];
        int end = (*row_ptr)[i + 1];
        for (int j = start; j < end; j++) {
            seed = seed * 1103515245u + 12345u;
            (*col_idx)[edge_idx++] = seed % N;
        }
        /* Connectivity edge */
        if (i < N - 1) {
            (*col_idx)[edge_idx++] = i + 1;
        }
    }

    /* Update row_ptr with connectivity edges */
    for (int i = 0; i < N; i++) {
        (*row_ptr)[i + 1] += (i < N - 1) ? (i + 1) : (N - 1);
    }
    /* Fix: recount properly */
    (*row_ptr)[0] = 0;
    int ptr = 0;
    for (int i = 0; i < N; i++) {
        seed = seed * 1103515245u + 12345u;
        int deg = 1 + (seed % (2 * avg_degree));
        if (i < N - 1) deg++;
        ptr += deg;
        (*row_ptr)[i + 1] = ptr;
    }
    nnz = ptr;

    /* Regenerate edges */
    unsigned int s2 = seed;
    edge_idx = 0;
    for (int i = 0; i < N; i++) {
        int deg = (*row_ptr)[i + 1] - (*row_ptr)[i];
        int has_conn = (i < N - 1) ? 1 : 0;
        for (int j = 0; j < deg - has_conn; j++) {
            s2 = s2 * 1103515245u + 12345u;
            (*col_idx)[edge_idx++] = s2 % N;
        }
        if (has_conn) {
            (*col_idx)[edge_idx++] = i + 1;
        }
    }

    *nnz_out = nnz;
}

int main(int argc, char **argv) {
    int N = 500;
    int avg_deg = 4;
    int source = 0;
    unsigned int seed = 42;

    for (int k = 1; k < argc; k++) {
        if (strcmp(argv[k], "--size") == 0 && k+1 < argc) N = atoi(argv[++k]);
        else if (strcmp(argv[k], "--degree") == 0 && k+1 < argc) avg_deg = atoi(argv[++k]);
        else if (strcmp(argv[k], "--source") == 0 && k+1 < argc) source = atoi(argv[++k]);
        else if (strcmp(argv[k], "--seed") == 0 && k+1 < argc) seed = (unsigned int)atoi(argv[++k]);
    }

    int *row_ptr, *col_idx;
    int nnz;
    generate_graph(N, avg_deg, seed, &row_ptr, &col_idx, &nnz);

    int *cpu_dist = (int *)malloc(N * sizeof(int));
    int *gpu_dist = (int *)malloc(N * sizeof(int));

    cpu_bfs(row_ptr, col_idx, cpu_dist, N, source);
    gpu_bfs(row_ptr, col_idx, gpu_dist, N, nnz, source);

    int mismatches = 0;
    int unvisited_cpu = 0, unvisited_gpu = 0;
    for (int i = 0; i < N; i++) {
        if (cpu_dist[i] == -1) unvisited_cpu++;
        if (gpu_dist[i] == -1) unvisited_gpu++;
        if (cpu_dist[i] != gpu_dist[i]) mismatches++;
    }

    printf("N=%d\n", N);
    printf("NNZ=%d\n", nnz);
    printf("SOURCE=%d\n", source);
    printf("MISMATCHES=%d\n", mismatches);
    printf("CPU_UNVISITED=%d\n", unvisited_cpu);
    printf("GPU_UNVISITED=%d\n", unvisited_gpu);
    printf("MATCH=%d\n", mismatches == 0 ? 1 : 0);

    free(row_ptr); free(col_idx); free(cpu_dist); free(gpu_dist);
    return mismatches == 0 ? 0 : 1;
}
