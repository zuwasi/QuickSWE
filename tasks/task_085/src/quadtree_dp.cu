#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define MAX_NODES 1024
#define MAX_DEPTH 5
#define CHILDREN_PER_NODE 4

// ---------------------------------------------------------------------------
// Quadtree node (stored as array-of-structs)
// ---------------------------------------------------------------------------
typedef struct {
    int parent;          // -1 for root
    int children[4];     // -1 if no child
    float value;         // leaf value or 0 for internal
    int is_leaf;
    int depth;
} QuadNode;

// ---------------------------------------------------------------------------
// CPU reference — recursive quadtree processing (DO NOT MODIFY)
// ---------------------------------------------------------------------------
float cpu_process_node(const QuadNode *nodes, int node_idx, float *results, int N) {
    if (node_idx < 0 || node_idx >= N) return 0.0f;

    const QuadNode *node = &nodes[node_idx];

    if (node->is_leaf) {
        results[node_idx] = node->value;
        return node->value;
    }

    float sum = 0.0f;
    for (int c = 0; c < 4; c++) {
        if (node->children[c] >= 0) {
            sum += cpu_process_node(nodes, node->children[c], results, N);
        }
    }
    results[node_idx] = sum;
    return sum;
}

void cpu_process_quadtree(const QuadNode *nodes, int N, float *results) {
    memset(results, 0, N * sizeof(float));
    cpu_process_node(nodes, 0, results, N);  // start from root
}

// ---------------------------------------------------------------------------
// GPU kernels with dynamic parallelism
// ---------------------------------------------------------------------------

// BUG 1: Child kernels write to the output buffer without synchronization.
//         Multiple children of different parents write concurrently to their
//         parent's result slot using non-atomic operations, causing data races.
//
// BUG 2: cudaDeviceSynchronize() in device code synchronizes ALL work on
//         the device, not just this thread's children. When multiple parent
//         threads call cudaDeviceSynchronize() concurrently, it can deadlock
//         because each parent waits for ALL device work (including other
//         parents' children) to complete, creating a circular dependency.
//
// The fix should:
// - Use per-parent streams for child launches
// - Use cudaStreamSynchronize() with the specific child stream instead of
//   cudaDeviceSynchronize()
// - Use atomicAdd or proper synchronization for writing results

__global__ void process_node_kernel(const QuadNode *nodes, float *results,
                                      int N, int node_idx);

__global__ void process_leaf_kernel(const QuadNode *nodes, float *results,
                                     int node_idx) {
    results[node_idx] = nodes[node_idx].value;
}

__global__ void process_node_kernel(const QuadNode *nodes, float *results,
                                      int N, int node_idx) {
    if (node_idx < 0 || node_idx >= N) return;

    const QuadNode *node = &nodes[node_idx];

    if (node->is_leaf) {
        results[node_idx] = node->value;
        return;
    }

    // Launch child kernels for each child node
    for (int c = 0; c < 4; c++) {
        int child = node->children[c];
        if (child >= 0 && child < N) {
            // BUG: All children launched on default stream (stream 0) which is
            // shared with parent. No explicit synchronization between launches.
            process_node_kernel<<<1, 1>>>(nodes, results, N, child);
        }
    }

    // BUG: cudaDeviceSynchronize() waits for ALL device work, not just
    // children of this thread. If multiple threads run this kernel
    // concurrently, they each wait for everyone else's children too,
    // potentially causing deadlock when the device is saturated.
    cudaDeviceSynchronize();

    // BUG: Race condition — reading child results that may not be written yet
    // (cudaDeviceSynchronize deadlocked or didn't actually wait for our children)
    float sum = 0.0f;
    for (int c = 0; c < 4; c++) {
        int child = node->children[c];
        if (child >= 0 && child < N) {
            sum += results[child];  // Non-atomic read of potentially racy data
        }
    }
    results[node_idx] = sum;
}

// BUG: This launcher processes multiple root-level nodes in parallel,
// each of which launches child kernels, greatly increasing deadlock risk.
__global__ void process_level_kernel(const QuadNode *nodes, float *results,
                                       int N, const int *level_nodes, int level_count) {
    int tid = blockIdx.x * blockDim.x + threadIdx.x;
    if (tid >= level_count) return;

    int node_idx = level_nodes[tid];
    if (node_idx < 0 || node_idx >= N) return;

    const QuadNode *node = &nodes[node_idx];

    if (node->is_leaf) {
        results[node_idx] = node->value;
        return;
    }

    // Launch children
    for (int c = 0; c < 4; c++) {
        int child = node->children[c];
        if (child >= 0 && child < N) {
            process_node_kernel<<<1, 1>>>(nodes, results, N, child);
        }
    }

    // BUG: Same cudaDeviceSynchronize() deadlock issue
    cudaDeviceSynchronize();

    float sum = 0.0f;
    for (int c = 0; c < 4; c++) {
        int child = node->children[c];
        if (child >= 0 && child < N) {
            sum += results[child];
        }
    }
    results[node_idx] = sum;
}

// ---------------------------------------------------------------------------
// GPU driver
// ---------------------------------------------------------------------------
void gpu_process_quadtree(const QuadNode *h_nodes, int N, float *h_results) {
    QuadNode *d_nodes;
    float *d_results;

    cudaMalloc(&d_nodes, N * sizeof(QuadNode));
    cudaMalloc(&d_results, N * sizeof(float));
    cudaMemcpy(d_nodes, h_nodes, N * sizeof(QuadNode), cudaMemcpyHostToDevice);
    cudaMemset(d_results, 0, N * sizeof(float));

    // Set device limits for dynamic parallelism
    cudaDeviceSetLimit(cudaLimitDevRuntimeSyncDepth, MAX_DEPTH + 1);
    cudaDeviceSetLimit(cudaLimitDevRuntimePendingLaunchCount, 2048);

    // Launch from root — single thread launches recursive children
    process_node_kernel<<<1, 1>>>(d_nodes, d_results, N, 0);

    cudaError_t err = cudaDeviceSynchronize();
    if (err != cudaSuccess) {
        fprintf(stderr, "GPU_ERROR=%d\n", (int)err);
        // Still try to copy what we have
    }

    cudaMemcpy(h_results, d_results, N * sizeof(float), cudaMemcpyDeviceToHost);

    cudaFree(d_nodes);
    cudaFree(d_results);
}

// Alternative: process level by level to test concurrent parent issue
void gpu_process_quadtree_parallel(const QuadNode *h_nodes, int N, float *h_results) {
    QuadNode *d_nodes;
    float *d_results;

    cudaMalloc(&d_nodes, N * sizeof(QuadNode));
    cudaMalloc(&d_results, N * sizeof(float));
    cudaMemcpy(d_nodes, h_nodes, N * sizeof(QuadNode), cudaMemcpyHostToDevice);
    cudaMemset(d_results, 0, N * sizeof(float));

    cudaDeviceSetLimit(cudaLimitDevRuntimeSyncDepth, MAX_DEPTH + 1);
    cudaDeviceSetLimit(cudaLimitDevRuntimePendingLaunchCount, 2048);

    // Find nodes at depth 1 (root's children)
    int level1_nodes[4];
    int level1_count = 0;
    for (int c = 0; c < 4; c++) {
        if (h_nodes[0].children[c] >= 0) {
            level1_nodes[level1_count++] = h_nodes[0].children[c];
        }
    }

    int *d_level_nodes;
    cudaMalloc(&d_level_nodes, level1_count * sizeof(int));
    cudaMemcpy(d_level_nodes, level1_nodes, level1_count * sizeof(int), cudaMemcpyHostToDevice);

    // Process root's children in parallel — this triggers the deadlock bug
    process_level_kernel<<<1, level1_count>>>(d_nodes, d_results, N,
                                                d_level_nodes, level1_count);

    cudaError_t err = cudaDeviceSynchronize();

    // Aggregate root
    float root_sum = 0.0f;
    float *tmp = (float *)malloc(N * sizeof(float));
    cudaMemcpy(tmp, d_results, N * sizeof(float), cudaMemcpyDeviceToHost);
    for (int c = 0; c < 4; c++) {
        if (h_nodes[0].children[c] >= 0) {
            root_sum += tmp[h_nodes[0].children[c]];
        }
    }
    tmp[0] = root_sum;
    memcpy(h_results, tmp, N * sizeof(float));

    if (err != cudaSuccess) {
        fprintf(stderr, "GPU_ERROR=%d\n", (int)err);
    }

    free(tmp);
    cudaFree(d_nodes); cudaFree(d_results); cudaFree(d_level_nodes);
}

// ---------------------------------------------------------------------------
// Tree generation
// ---------------------------------------------------------------------------
int build_quadtree(QuadNode *nodes, int max_nodes, int depth, int max_depth,
                    int parent, unsigned int *seed_state) {
    static int next_id = 0;
    if (parent == -1) next_id = 0;  // reset for root

    int id = next_id++;
    if (id >= max_nodes) return -1;

    nodes[id].parent = parent;
    nodes[id].depth = depth;

    if (depth >= max_depth) {
        // Leaf
        nodes[id].is_leaf = 1;
        nodes[id].value = (float)((*seed_state = *seed_state * 1103515245 + 12345) % 100) / 10.0f;
        for (int c = 0; c < 4; c++) nodes[id].children[c] = -1;
    } else {
        nodes[id].is_leaf = 0;
        nodes[id].value = 0.0f;
        // Create 2-4 children
        int n_children = 2 + (*seed_state = *seed_state * 1103515245 + 12345) % 3;
        for (int c = 0; c < 4; c++) {
            if (c < n_children && next_id < max_nodes) {
                nodes[id].children[c] = build_quadtree(nodes, max_nodes,
                    depth + 1, max_depth, id, seed_state);
            } else {
                nodes[id].children[c] = -1;
            }
        }
    }
    return id;
}

// ---------------------------------------------------------------------------
int main(int argc, char **argv) {
    int max_depth = 2;
    unsigned int seed = 42;
    int parallel_mode = 0;

    for (int k = 1; k < argc; k++) {
        if (strcmp(argv[k], "--depth") == 0 && k+1 < argc) max_depth = atoi(argv[++k]);
        else if (strcmp(argv[k], "--seed") == 0 && k+1 < argc) seed = (unsigned int)atoi(argv[++k]);
        else if (strcmp(argv[k], "--parallel") == 0) parallel_mode = 1;
    }

    if (max_depth > MAX_DEPTH) max_depth = MAX_DEPTH;

    QuadNode *nodes = (QuadNode *)calloc(MAX_NODES, sizeof(QuadNode));
    unsigned int seed_state = seed;
    build_quadtree(nodes, MAX_NODES, 0, max_depth, -1, &seed_state);

    // Count actual nodes
    int N = 0;
    for (int i = 0; i < MAX_NODES; i++) {
        if (i == 0 || nodes[i].parent >= 0 || nodes[i].is_leaf) N = i + 1;
        else break;
    }
    // More robust counting
    N = 0;
    for (int i = 0; i < MAX_NODES; i++) {
        if (nodes[i].depth > 0 || i == 0) N++;
        else break;
    }

    float *cpu_results = (float *)calloc(N, sizeof(float));
    float *gpu_results = (float *)calloc(N, sizeof(float));

    cpu_process_quadtree(nodes, N, cpu_results);

    if (parallel_mode) {
        gpu_process_quadtree_parallel(nodes, N, gpu_results);
    } else {
        gpu_process_quadtree(nodes, N, gpu_results);
    }

    // Compare
    int mismatches = 0;
    int first_bad = -1;
    float max_error = 0.0f;
    for (int i = 0; i < N; i++) {
        float err = fabsf(cpu_results[i] - gpu_results[i]);
        if (err > max_error) max_error = err;
        if (err > 0.01f) {
            if (first_bad < 0) first_bad = i;
            mismatches++;
        }
    }

    // Check root value (most important)
    float root_err = fabsf(cpu_results[0] - gpu_results[0]);

    printf("DEPTH=%d\n", max_depth);
    printf("NODES=%d\n", N);
    printf("PARALLEL=%d\n", parallel_mode);
    printf("CPU_ROOT=%.4f\n", cpu_results[0]);
    printf("GPU_ROOT=%.4f\n", gpu_results[0]);
    printf("ROOT_ERROR=%.6e\n", root_err);
    printf("MISMATCHES=%d\n", mismatches);
    printf("MAX_ERROR=%.6e\n", max_error);
    if (first_bad >= 0) {
        printf("FIRST_BAD=%d\n", first_bad);
        printf("EXPECTED=%.4f\n", cpu_results[first_bad]);
        printf("GOT=%.4f\n", gpu_results[first_bad]);
    }
    printf("ROOT_OK=%d\n", root_err < 0.01f ? 1 : 0);
    printf("MATCH=%d\n", (mismatches == 0 && root_err < 0.01f) ? 1 : 0);

    free(nodes); free(cpu_results); free(gpu_results);
    return (mismatches == 0) ? 0 : 1;
}
