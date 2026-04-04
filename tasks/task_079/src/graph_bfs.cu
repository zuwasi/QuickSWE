#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define BLOCK_SIZE 256
#define INF (-1)

// ---------------------------------------------------------------------------
// CSR graph structure
// ---------------------------------------------------------------------------
typedef struct {
    int num_nodes;
    int num_edges;
    int *row_offsets;   // size = num_nodes + 1
    int *col_indices;   // size = num_edges
} CSRGraph;

// ---------------------------------------------------------------------------
// CPU BFS reference (DO NOT MODIFY)
// ---------------------------------------------------------------------------
void cpu_bfs(const CSRGraph *g, int source, int *distances) {
    for (int i = 0; i < g->num_nodes; i++) distances[i] = INF;
    distances[source] = 0;

    // Simple queue-based BFS
    int *queue = (int *)malloc(g->num_nodes * sizeof(int));
    int head = 0, tail = 0;
    queue[tail++] = source;

    while (head < tail) {
        int node = queue[head++];
        int start = g->row_offsets[node];
        int end   = g->row_offsets[node + 1];
        for (int e = start; e < end; e++) {
            int neighbor = g->col_indices[e];
            if (distances[neighbor] == INF) {
                distances[neighbor] = distances[node] + 1;
                queue[tail++] = neighbor;
            }
        }
    }
    free(queue);
}

// ---------------------------------------------------------------------------
// GPU BFS kernel — BUGGY
// ---------------------------------------------------------------------------

/*
 * Uses a frontier-based approach: two arrays act as ping-pong frontiers.
 * Each BFS level, the kernel reads the current frontier, discovers new
 * nodes, and appends them to the next frontier.
 *
 * BUG 1 — Frontier counter not reset:
 *   The counter for the new frontier (`d_next_count`) is never reset to
 *   0 between levels.  Instead, it keeps accumulating, so previously
 *   visited nodes remain in the frontier and are re-processed every
 *   level.  This causes exponential slowdown and may overwrite distances
 *   with longer paths.
 *
 * BUG 2 — Non-atomic visited check:
 *   The kernel does:
 *       if (distances[neighbor] == INF) {
 *           distances[neighbor] = level + 1;
 *           // add to frontier
 *       }
 *   This is a classic TOCTOU race: two threads can both see INF,
 *   both write the distance, and both add the neighbor to the frontier.
 *   This causes duplicate frontier entries (wasting work) and potential
 *   wrong distances if a later-level thread wins the race.
 */

__global__ void bfs_kernel(const int *row_offsets, const int *col_indices,
                           int *distances,
                           const int *curr_frontier, int curr_count,
                           int *next_frontier, int *d_next_count,
                           int level, int num_nodes) {
    int tid = blockIdx.x * blockDim.x + threadIdx.x;
    if (tid >= curr_count) return;

    int node = curr_frontier[tid];
    int start = row_offsets[node];
    int end   = row_offsets[node + 1];

    for (int e = start; e < end; e++) {
        int neighbor = col_indices[e];
        // BUG 2: non-atomic read-then-write
        if (distances[neighbor] == INF) {
            distances[neighbor] = level + 1;
            int pos = atomicAdd(d_next_count, 1);
            if (pos < num_nodes) {
                next_frontier[pos] = neighbor;
            }
        }
    }
}

// ---------------------------------------------------------------------------
// Host BFS driver — BUGGY
// ---------------------------------------------------------------------------
void gpu_bfs(const CSRGraph *h_graph, int source, int *h_distances) {
    int N = h_graph->num_nodes;
    int E = h_graph->num_edges;

    // Upload graph to device
    int *d_row_offsets, *d_col_indices;
    cudaMalloc(&d_row_offsets, (N + 1) * sizeof(int));
    cudaMalloc(&d_col_indices, E * sizeof(int));
    cudaMemcpy(d_row_offsets, h_graph->row_offsets,
               (N + 1) * sizeof(int), cudaMemcpyHostToDevice);
    cudaMemcpy(d_col_indices, h_graph->col_indices,
               E * sizeof(int), cudaMemcpyHostToDevice);

    // Distances
    int *d_distances;
    cudaMalloc(&d_distances, N * sizeof(int));
    // Initialize all to INF
    cudaMemset(d_distances, 0xFF, N * sizeof(int));  // sets to -1 (all bits 1)
    int zero = 0;
    cudaMemcpy(&d_distances[source], &zero, sizeof(int),
               cudaMemcpyHostToDevice);

    // Frontiers (ping-pong)
    int *d_frontier0, *d_frontier1;
    cudaMalloc(&d_frontier0, N * sizeof(int));
    cudaMalloc(&d_frontier1, N * sizeof(int));

    // Counter for next frontier
    int *d_next_count;
    cudaMalloc(&d_next_count, sizeof(int));

    // Initialize first frontier with source
    cudaMemcpy(d_frontier0, &source, sizeof(int), cudaMemcpyHostToDevice);
    int curr_count = 1;

    int *curr_frontier = d_frontier0;
    int *next_frontier = d_frontier1;

    int level = 0;
    int max_levels = N;  // safety bound

    // BUG 1: d_next_count is set once here but NEVER reset inside the loop
    int initial_zero = 0;
    cudaMemcpy(d_next_count, &initial_zero, sizeof(int),
               cudaMemcpyHostToDevice);

    while (curr_count > 0 && level < max_levels) {
        int grid = (curr_count + BLOCK_SIZE - 1) / BLOCK_SIZE;

        // BUG 1: Should reset d_next_count to 0 HERE, but we don't.
        // cudaMemcpy(d_next_count, &initial_zero, sizeof(int),
        //            cudaMemcpyHostToDevice);

        bfs_kernel<<<grid, BLOCK_SIZE>>>(
            d_row_offsets, d_col_indices, d_distances,
            curr_frontier, curr_count,
            next_frontier, d_next_count,
            level, N);
        cudaDeviceSynchronize();

        // Read next frontier count
        int next_count;
        cudaMemcpy(&next_count, d_next_count, sizeof(int),
                   cudaMemcpyDeviceToHost);

        // Clamp to prevent buffer overflow
        if (next_count > N) next_count = N;

        // Swap frontiers
        int *tmp = curr_frontier;
        curr_frontier = next_frontier;
        next_frontier = tmp;

        curr_count = next_count;
        level++;
    }

    // Copy distances back
    cudaMemcpy(h_distances, d_distances, N * sizeof(int),
               cudaMemcpyDeviceToHost);

    cudaFree(d_row_offsets);
    cudaFree(d_col_indices);
    cudaFree(d_distances);
    cudaFree(d_frontier0);
    cudaFree(d_frontier1);
    cudaFree(d_next_count);
}

// ---------------------------------------------------------------------------
// Random graph generator (connected undirected)
// ---------------------------------------------------------------------------
void generate_random_graph(CSRGraph *g, int num_nodes, int num_edges,
                           unsigned int seed) {
    srand(seed);
    g->num_nodes = num_nodes;

    // Build edge list (undirected → 2 directed edges per undirected edge)
    int max_directed = num_edges * 2 + (num_nodes - 1) * 2;
    int *src = (int *)malloc(max_directed * sizeof(int));
    int *dst = (int *)malloc(max_directed * sizeof(int));
    int count = 0;

    // First, create a spanning tree to ensure connectivity
    for (int i = 1; i < num_nodes; i++) {
        int j = rand() % i;
        src[count] = i; dst[count] = j; count++;
        src[count] = j; dst[count] = i; count++;
    }

    // Add random edges
    for (int e = 0; e < num_edges - (num_nodes - 1); e++) {
        int u = rand() % num_nodes;
        int v = rand() % num_nodes;
        if (u == v) continue;
        src[count] = u; dst[count] = v; count++;
        src[count] = v; dst[count] = u; count++;
    }

    g->num_edges = count;

    // Sort by source for CSR construction
    // Simple bucket sort
    int *degree = (int *)calloc(num_nodes, sizeof(int));
    for (int i = 0; i < count; i++) degree[src[i]]++;

    g->row_offsets = (int *)malloc((num_nodes + 1) * sizeof(int));
    g->row_offsets[0] = 0;
    for (int i = 0; i < num_nodes; i++) {
        g->row_offsets[i + 1] = g->row_offsets[i] + degree[i];
    }

    g->col_indices = (int *)malloc(count * sizeof(int));
    int *pos = (int *)calloc(num_nodes, sizeof(int));
    for (int i = 0; i < count; i++) {
        int s = src[i];
        int offset = g->row_offsets[s] + pos[s];
        g->col_indices[offset] = dst[i];
        pos[s]++;
    }

    free(src);
    free(dst);
    free(degree);
    free(pos);
}

void free_graph(CSRGraph *g) {
    free(g->row_offsets);
    free(g->col_indices);
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
int main(int argc, char **argv) {
    int num_nodes = 100;
    int num_edges = 500;
    unsigned int seed = 42;
    int source = 0;

    for (int k = 1; k < argc; k++) {
        if (strcmp(argv[k], "--nodes") == 0 && k + 1 < argc)
            num_nodes = atoi(argv[++k]);
        else if (strcmp(argv[k], "--edges") == 0 && k + 1 < argc)
            num_edges = atoi(argv[++k]);
        else if (strcmp(argv[k], "--seed") == 0 && k + 1 < argc)
            seed = (unsigned int)atoi(argv[++k]);
        else if (strcmp(argv[k], "--source") == 0 && k + 1 < argc)
            source = atoi(argv[++k]);
    }

    if (num_edges < num_nodes - 1) num_edges = num_nodes - 1;

    CSRGraph graph;
    generate_random_graph(&graph, num_nodes, num_edges, seed);

    int *cpu_dist = (int *)malloc(num_nodes * sizeof(int));
    int *gpu_dist = (int *)malloc(num_nodes * sizeof(int));

    cpu_bfs(&graph, source, cpu_dist);
    gpu_bfs(&graph, source, gpu_dist);

    int mismatches = 0;
    int first_bad = -1;
    int reachable = 0;
    int wrong_shorter = 0;
    int wrong_longer = 0;

    for (int i = 0; i < num_nodes; i++) {
        if (cpu_dist[i] != INF) reachable++;
        if (cpu_dist[i] != gpu_dist[i]) {
            if (first_bad < 0) first_bad = i;
            mismatches++;
            if (gpu_dist[i] != INF && cpu_dist[i] != INF) {
                if (gpu_dist[i] < cpu_dist[i]) wrong_shorter++;
                else wrong_longer++;
            }
        }
    }

    int match = (mismatches == 0) ? 1 : 0;

    printf("NODES=%d\n", num_nodes);
    printf("EDGES=%d\n", graph.num_edges);
    printf("REACHABLE=%d\n", reachable);
    printf("MISMATCHES=%d\n", mismatches);
    printf("WRONG_SHORTER=%d\n", wrong_shorter);
    printf("WRONG_LONGER=%d\n", wrong_longer);
    if (first_bad >= 0) {
        printf("FIRST_BAD_NODE=%d\n", first_bad);
        printf("EXPECTED_DIST=%d\n", cpu_dist[first_bad]);
        printf("GOT_DIST=%d\n", gpu_dist[first_bad]);
    }
    printf("MATCH=%d\n", match);

    free(cpu_dist);
    free(gpu_dist);
    free_graph(&graph);
    return match ? 0 : 1;
}
