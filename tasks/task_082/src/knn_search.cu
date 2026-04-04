#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <float.h>

#define BLOCK_SIZE 256
#define MAX_K 64
#define TILE_SIZE 128
#define DIMS 16

// ---------------------------------------------------------------------------
// CPU reference k-NN (DO NOT MODIFY)
// ---------------------------------------------------------------------------
static float cpu_distance(const float *a, const float *b, int dims) {
    float d = 0.0f;
    for (int i = 0; i < dims; i++) {
        float diff = a[i] - b[i];
        d += diff * diff;
    }
    return d;
}

typedef struct {
    float dist;
    int idx;
} DistIdx;

static int distidx_cmp(const void *a, const void *b) {
    float da = ((const DistIdx *)a)->dist;
    float db = ((const DistIdx *)b)->dist;
    if (da < db) return -1;
    if (da > db) return 1;
    return 0;
}

void cpu_knn(const float *queries, int n_queries, int dims,
             const float *dataset, int n_dataset,
             int k, int *out_indices, float *out_distances) {
    int actual_k = k < n_dataset ? k : n_dataset;
    DistIdx *dists = (DistIdx *)malloc(n_dataset * sizeof(DistIdx));

    for (int q = 0; q < n_queries; q++) {
        const float *query = queries + q * dims;
        for (int d = 0; d < n_dataset; d++) {
            dists[d].dist = cpu_distance(query, dataset + d * dims, dims);
            dists[d].idx = d;
        }
        qsort(dists, n_dataset, sizeof(DistIdx), distidx_cmp);
        for (int j = 0; j < k; j++) {
            if (j < actual_k) {
                out_indices[q * k + j] = dists[j].idx;
                out_distances[q * k + j] = dists[j].dist;
            } else {
                out_indices[q * k + j] = -1;
                out_distances[q * k + j] = FLT_MAX;
            }
        }
    }
    free(dists);
}

// ---------------------------------------------------------------------------
// GPU distance computation kernel (exists, brute-force O(N*M))
// ---------------------------------------------------------------------------
__global__ void compute_distance_matrix(const float *queries, int n_queries,
                                         const float *dataset, int n_dataset,
                                         int dims, float *dist_matrix) {
    int q = blockIdx.y * blockDim.y + threadIdx.y;
    int d = blockIdx.x * blockDim.x + threadIdx.x;

    if (q >= n_queries || d >= n_dataset) return;

    float dist = 0.0f;
    for (int i = 0; i < dims; i++) {
        float diff = queries[q * dims + i] - dataset[d * dims + i];
        dist += diff * diff;
    }
    dist_matrix[q * n_dataset + d] = dist;
}

// ---------------------------------------------------------------------------
// GPU k-NN search — STUB (to be implemented)
// ---------------------------------------------------------------------------

// TODO: Implement a k-NN kernel using a max-heap of size k per query.
// Each thread should process one query point:
//   1. Initialize a max-heap of size k with FLT_MAX distances.
//   2. Iterate over dataset points in tiles loaded into shared memory.
//   3. For each dataset point, compute distance. If distance < heap max,
//      replace heap root and sift down.
//   4. After processing all dataset points, extract sorted k-NN from heap.
//
// Handle k > n_dataset: fill remaining slots with index=-1, dist=FLT_MAX.

void gpu_knn_search(const float *h_queries, int n_queries, int dims,
                    const float *h_dataset, int n_dataset,
                    int k, int *h_out_indices, float *h_out_distances) {
    // STUB: returns first k indices — obviously wrong
    for (int q = 0; q < n_queries; q++) {
        for (int j = 0; j < k; j++) {
            h_out_indices[q * k + j] = j < n_dataset ? j : -1;
            h_out_distances[q * k + j] = j < n_dataset ? 0.0f : FLT_MAX;
        }
    }
}

// ---------------------------------------------------------------------------
// Verification
// ---------------------------------------------------------------------------
int main(int argc, char **argv) {
    int n_queries = 50;
    int n_dataset = 500;
    int dims = DIMS;
    int k = 5;
    unsigned int seed = 42;

    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--queries") == 0 && i+1 < argc) n_queries = atoi(argv[++i]);
        else if (strcmp(argv[i], "--dataset") == 0 && i+1 < argc) n_dataset = atoi(argv[++i]);
        else if (strcmp(argv[i], "--dims") == 0 && i+1 < argc) dims = atoi(argv[++i]);
        else if (strcmp(argv[i], "--k") == 0 && i+1 < argc) k = atoi(argv[++i]);
        else if (strcmp(argv[i], "--seed") == 0 && i+1 < argc) seed = (unsigned int)atoi(argv[++i]);
    }

    int actual_k = k < n_dataset ? k : n_dataset;

    float *queries = (float *)malloc(n_queries * dims * sizeof(float));
    float *dataset = (float *)malloc(n_dataset * dims * sizeof(float));
    int *cpu_indices = (int *)malloc(n_queries * k * sizeof(int));
    float *cpu_dists = (float *)malloc(n_queries * k * sizeof(float));
    int *gpu_indices = (int *)malloc(n_queries * k * sizeof(int));
    float *gpu_dists = (float *)malloc(n_queries * k * sizeof(float));

    srand(seed);
    for (int i = 0; i < n_queries * dims; i++)
        queries[i] = ((float)rand() / RAND_MAX) * 100.0f;
    for (int i = 0; i < n_dataset * dims; i++)
        dataset[i] = ((float)rand() / RAND_MAX) * 100.0f;

    cpu_knn(queries, n_queries, dims, dataset, n_dataset, k, cpu_indices, cpu_dists);
    gpu_knn_search(queries, n_queries, dims, dataset, n_dataset, k, gpu_indices, gpu_dists);

    // Check: for each query, the k-NN sets should match
    int index_mismatches = 0;
    int dist_mismatches = 0;
    int first_bad_query = -1;

    for (int q = 0; q < n_queries; q++) {
        for (int j = 0; j < actual_k; j++) {
            int ci = cpu_indices[q * k + j];
            int gi = gpu_indices[q * k + j];
            float cd = cpu_dists[q * k + j];
            float gd = gpu_dists[q * k + j];

            if (ci != gi) {
                // Indices might differ if distances are equal — check distance
                if (fabsf(cd - gd) > 1e-3f) {
                    index_mismatches++;
                    if (first_bad_query < 0) first_bad_query = q;
                }
            }
            if (fabsf(cd - gd) > 1e-3f) {
                dist_mismatches++;
            }
        }
    }

    // Check k > n_dataset padding
    int padding_ok = 1;
    if (k > n_dataset) {
        for (int q = 0; q < n_queries; q++) {
            for (int j = n_dataset; j < k; j++) {
                if (gpu_indices[q * k + j] != -1) padding_ok = 0;
                if (gpu_dists[q * k + j] < FLT_MAX * 0.9f) padding_ok = 0;
            }
        }
    }

    printf("N_QUERIES=%d\n", n_queries);
    printf("N_DATASET=%d\n", n_dataset);
    printf("K=%d\n", k);
    printf("INDEX_MISMATCHES=%d\n", index_mismatches);
    printf("DIST_MISMATCHES=%d\n", dist_mismatches);
    printf("PADDING_OK=%d\n", padding_ok);
    if (first_bad_query >= 0) {
        printf("FIRST_BAD_QUERY=%d\n", first_bad_query);
    }
    printf("MATCH=%d\n", (index_mismatches == 0 && dist_mismatches == 0 && padding_ok) ? 1 : 0);

    free(queries); free(dataset);
    free(cpu_indices); free(cpu_dists);
    free(gpu_indices); free(gpu_dists);
    return 0;
}
