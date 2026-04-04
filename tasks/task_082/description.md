# Feature Request: Implement Efficient CUDA k-Nearest Neighbors

## Summary

The `knn_search.cu` file contains:

- A working **CPU reference** k-NN implementation (`cpu_knn`).
- A **brute-force distance computation kernel** that computes the full N×M
  distance matrix between query points and dataset points.
- A **stubbed** `gpu_knn_search()` function that currently returns the first k
  indices for every query (obviously wrong).

Implement an efficient GPU k-NN that:

1. For each query point, finds the k nearest dataset points.
2. Uses a **max-heap of size k** per query to avoid sorting the full distance
   array — maintain a heap of the k smallest distances seen so far, replacing
   the max when a smaller distance is found.
3. Uses **shared memory** to hold candidate lists and dataset tiles.
4. Handles edge case where k > number of dataset points gracefully (return
   all points, padded with -1 indices and FLT_MAX distances).

## Acceptance Criteria

- Results match CPU reference for k=1, k=5, k=10 with dataset sizes 100,
  500, 1000, and 2000.
- k > N_dataset handled without crash, returns valid subset.
- No full sort of the distance array — must use partial selection.

## Current State

```c
void gpu_knn_search(const float *queries, int n_queries, int dims,
                    const float *dataset, int n_dataset,
                    int k, int *out_indices, float *out_distances) {
    // TODO: implement k-NN with max-heap selection
    for (int q = 0; q < n_queries; q++) {
        for (int j = 0; j < k; j++) {
            out_indices[q * k + j] = j < n_dataset ? j : -1;
            out_distances[q * k + j] = j < n_dataset ? 0.0f : FLT_MAX;
        }
    }
}
```

## Environment

- CUDA Toolkit 12.x, any NVIDIA GPU with compute capability >= 3.5
