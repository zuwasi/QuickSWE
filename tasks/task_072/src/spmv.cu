#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define BLOCK_SIZE 256

// ---------------------------------------------------------------------------
// CPU reference SpMV in CSR format (DO NOT MODIFY)
// ---------------------------------------------------------------------------
void cpu_spmv(const int *row_ptr, const int *col_idx, const float *values,
              const float *x, float *y, int num_rows) {
    for (int r = 0; r < num_rows; r++) {
        float sum = 0.0f;
        for (int j = row_ptr[r]; j < row_ptr[r + 1]; j++) {
            sum += values[j] * x[col_idx[j]];
        }
        y[r] = sum;
    }
}

// ---------------------------------------------------------------------------
// CUDA SpMV kernel — BUGGY
// ---------------------------------------------------------------------------
__global__ void spmv_kernel(const int *row_ptr, const int *col_idx,
                             const float *values, const float *x, float *y,
                             int num_rows, int nnz) {
    int row = blockIdx.x * blockDim.x + threadIdx.x;
    if (row >= num_rows) return;

    // BUG 1: Special-cases the last row using nnz instead of row_ptr[row+1].
    // The host code passes a WRONG nnz value (off by the number of empty rows).
    // The correct fix is to just always use row_ptr[row+1].
    int start = row_ptr[row];
    int end = (row == num_rows - 1) ? nnz : row_ptr[row + 1];

    // BUG 2: No initialisation of sum — if start == end (empty row) the
    // output y[row] is never written, leaving garbage from uninitialised
    // device memory.
    float sum;  // BUG: should be = 0.0f
    for (int j = start; j < end; j++) {
        sum += values[j] * x[col_idx[j]];
    }
    y[row] = sum;
}

// ---------------------------------------------------------------------------
// GPU SpMV wrapper — BUGGY (passes wrong nnz)
// ---------------------------------------------------------------------------
void gpu_spmv(const int *h_row_ptr, const int *h_col_idx,
              const float *h_values, const float *h_x, float *h_y,
              int num_rows, int nnz) {

    int *d_row_ptr, *d_col_idx;
    float *d_values, *d_x, *d_y;

    cudaMalloc(&d_row_ptr, (num_rows + 1) * sizeof(int));
    cudaMalloc(&d_col_idx, nnz * sizeof(int));
    cudaMalloc(&d_values, nnz * sizeof(float));
    cudaMalloc(&d_x, num_rows * sizeof(float));  // assumes square matrix
    cudaMalloc(&d_y, num_rows * sizeof(float));

    cudaMemcpy(d_row_ptr, h_row_ptr, (num_rows + 1) * sizeof(int), cudaMemcpyHostToDevice);
    cudaMemcpy(d_col_idx, h_col_idx, nnz * sizeof(int), cudaMemcpyHostToDevice);
    cudaMemcpy(d_values, h_values, nnz * sizeof(float), cudaMemcpyHostToDevice);
    cudaMemcpy(d_x, h_x, num_rows * sizeof(float), cudaMemcpyHostToDevice);

    // BUG 1 (host side): pass nnz - 1 instead of nnz, so the kernel's
    // special case for the last row uses the wrong end pointer.
    int grid = (num_rows + BLOCK_SIZE - 1) / BLOCK_SIZE;
    spmv_kernel<<<grid, BLOCK_SIZE>>>(d_row_ptr, d_col_idx, d_values,
                                       d_x, d_y, num_rows, nnz - 1);
    cudaDeviceSynchronize();

    cudaMemcpy(h_y, d_y, num_rows * sizeof(float), cudaMemcpyDeviceToHost);

    cudaFree(d_row_ptr);
    cudaFree(d_col_idx);
    cudaFree(d_values);
    cudaFree(d_x);
    cudaFree(d_y);
}

// ---------------------------------------------------------------------------
// Matrix generation helpers
// ---------------------------------------------------------------------------

// Build a sparse matrix in CSR format.  mode:
//   "identity" — N×N identity matrix
//   "random"   — random sparse matrix with ~density fraction of non-zeros
//   "empty"    — every other row is empty
void build_matrix(const char *mode, int N, float density, unsigned int seed,
                  int **row_ptr, int **col_idx, float **values, int *nnz_out) {
    srand(seed);

    if (strcmp(mode, "identity") == 0) {
        int nnz = N;
        *row_ptr = (int *)malloc((N + 1) * sizeof(int));
        *col_idx = (int *)malloc(nnz * sizeof(int));
        *values  = (float *)malloc(nnz * sizeof(float));
        for (int i = 0; i <= N; i++) (*row_ptr)[i] = i;
        for (int i = 0; i < N; i++) {
            (*col_idx)[i] = i;
            (*values)[i]  = 1.0f;
        }
        *nnz_out = nnz;

    } else if (strcmp(mode, "empty") == 0) {
        // Every other row is empty
        int nnz = 0;
        *row_ptr = (int *)malloc((N + 1) * sizeof(int));
        // First pass: count
        for (int r = 0; r < N; r++) {
            (*row_ptr)[r] = nnz;
            if (r % 2 == 0) {
                // put one element on the diagonal
                nnz++;
            }
        }
        (*row_ptr)[N] = nnz;
        *col_idx = (int *)malloc(nnz * sizeof(int));
        *values  = (float *)malloc(nnz * sizeof(float));
        int pos = 0;
        for (int r = 0; r < N; r++) {
            if (r % 2 == 0) {
                (*col_idx)[pos] = r;
                (*values)[pos]  = (float)(r + 1);
                pos++;
            }
        }
        *nnz_out = nnz;

    } else {
        // Random sparse
        // First pass: decide which entries are non-zero
        int capacity = (int)(N * N * density) + N;
        *col_idx = (int *)malloc(capacity * sizeof(int));
        *values  = (float *)malloc(capacity * sizeof(float));
        *row_ptr = (int *)malloc((N + 1) * sizeof(int));
        int nnz = 0;
        for (int r = 0; r < N; r++) {
            (*row_ptr)[r] = nnz;
            for (int c = 0; c < N; c++) {
                if ((float)rand() / RAND_MAX < density) {
                    (*col_idx)[nnz] = c;
                    (*values)[nnz]  = (float)(rand() % 100) / 10.0f;
                    nnz++;
                }
            }
        }
        (*row_ptr)[N] = nnz;
        *nnz_out = nnz;
    }
}

// ---------------------------------------------------------------------------
int main(int argc, char **argv) {
    int N = 100;
    float density = 0.1f;
    unsigned int seed = 42;
    const char *mode = "random";

    for (int k = 1; k < argc; k++) {
        if (strcmp(argv[k], "--size") == 0 && k + 1 < argc) {
            N = atoi(argv[++k]);
        } else if (strcmp(argv[k], "--density") == 0 && k + 1 < argc) {
            density = (float)atof(argv[++k]);
        } else if (strcmp(argv[k], "--seed") == 0 && k + 1 < argc) {
            seed = (unsigned int)atoi(argv[++k]);
        } else if (strcmp(argv[k], "--mode") == 0 && k + 1 < argc) {
            mode = argv[++k];
        }
    }

    int *row_ptr, *col_idx;
    float *values;
    int nnz;
    build_matrix(mode, N, density, seed, &row_ptr, &col_idx, &values, &nnz);

    // Input vector x
    float *x = (float *)malloc(N * sizeof(float));
    for (int i = 0; i < N; i++) {
        x[i] = (float)(rand() % 100) / 10.0f;
    }

    float *cpu_y = (float *)malloc(N * sizeof(float));
    float *gpu_y = (float *)malloc(N * sizeof(float));

    cpu_spmv(row_ptr, col_idx, values, x, cpu_y, N);
    gpu_spmv(row_ptr, col_idx, values, x, gpu_y, N, nnz);

    int mismatches = 0;
    float max_rel_err = 0.0f;
    int first_bad = -1;
    for (int i = 0; i < N; i++) {
        float diff = fabsf(cpu_y[i] - gpu_y[i]);
        float ref = fabsf(cpu_y[i]);
        float rel = (ref > 1e-8f) ? diff / ref : diff;
        if (rel > max_rel_err) max_rel_err = rel;
        if (rel > 1e-5f) {
            if (first_bad < 0) first_bad = i;
            mismatches++;
        }
    }

    printf("SIZE=%d\n", N);
    printf("NNZ=%d\n", nnz);
    printf("MODE=%s\n", mode);
    printf("MISMATCHES=%d\n", mismatches);
    printf("MAX_REL_ERR=%.8f\n", max_rel_err);
    if (first_bad >= 0) {
        printf("FIRST_BAD_ROW=%d\n", first_bad);
        printf("EXPECTED=%.6f\n", cpu_y[first_bad]);
        printf("GOT=%.6f\n", gpu_y[first_bad]);
    }
    printf("MATCH=%d\n", mismatches == 0 ? 1 : 0);

    free(row_ptr);
    free(col_idx);
    free(values);
    free(x);
    free(cpu_y);
    free(gpu_y);
    return mismatches == 0 ? 0 : 1;
}
