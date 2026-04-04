#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define BLOCK_SIZE 256
#define MAX_ROW_NNZ 512

// ---------------------------------------------------------------------------
// CSR sparse matrix representation
// ---------------------------------------------------------------------------
typedef struct {
    int rows, cols;
    int nnz;
    int *row_ptr;   // size rows+1
    int *col_idx;   // size nnz
    float *values;  // size nnz
} CSRMatrix;

CSRMatrix* csr_alloc(int rows, int cols, int nnz) {
    CSRMatrix *m = (CSRMatrix *)malloc(sizeof(CSRMatrix));
    m->rows = rows; m->cols = cols; m->nnz = nnz;
    m->row_ptr = (int *)calloc(rows + 1, sizeof(int));
    m->col_idx = (int *)malloc(nnz * sizeof(int));
    m->values  = (float *)malloc(nnz * sizeof(float));
    return m;
}

void csr_free(CSRMatrix *m) {
    if (m) { free(m->row_ptr); free(m->col_idx); free(m->values); free(m); }
}

// ---------------------------------------------------------------------------
// CPU reference SpGEMM (DO NOT MODIFY)
// ---------------------------------------------------------------------------
CSRMatrix* cpu_spgemm(const CSRMatrix *A, const CSRMatrix *B) {
    int M = A->rows;
    int N = B->cols;

    // Phase 1: compute result using dense accumulator per row
    float *acc = (float *)calloc(N, sizeof(float));
    int *marker = (int *)malloc(N * sizeof(int));
    memset(marker, -1, N * sizeof(int));

    // Count phase
    int *row_nnz = (int *)calloc(M, sizeof(int));
    for (int i = 0; i < M; i++) {
        // Clear
        for (int jj = A->row_ptr[i]; jj < A->row_ptr[i+1]; jj++) {
            int k = A->col_idx[jj];
            for (int kk = B->row_ptr[k]; kk < B->row_ptr[k+1]; kk++) {
                int j = B->col_idx[kk];
                acc[j] += A->values[jj] * B->values[kk];
                if (marker[j] != i) {
                    marker[j] = i;
                }
            }
        }
        for (int j = 0; j < N; j++) {
            if (fabsf(acc[j]) > 1e-10f) row_nnz[i]++;
            acc[j] = 0.0f;
        }
    }

    // Allocate output
    int total_nnz = 0;
    int *out_rowptr = (int *)calloc(M + 1, sizeof(int));
    for (int i = 0; i < M; i++) {
        out_rowptr[i+1] = out_rowptr[i] + row_nnz[i];
    }
    total_nnz = out_rowptr[M];

    CSRMatrix *C = csr_alloc(M, N, total_nnz);
    memcpy(C->row_ptr, out_rowptr, (M+1) * sizeof(int));

    // Fill phase
    memset(marker, -1, N * sizeof(int));
    for (int i = 0; i < M; i++) {
        int pos = C->row_ptr[i];
        for (int jj = A->row_ptr[i]; jj < A->row_ptr[i+1]; jj++) {
            int k = A->col_idx[jj];
            for (int kk = B->row_ptr[k]; kk < B->row_ptr[k+1]; kk++) {
                int j = B->col_idx[kk];
                acc[j] += A->values[jj] * B->values[kk];
            }
        }
        for (int j = 0; j < N; j++) {
            if (fabsf(acc[j]) > 1e-10f) {
                C->col_idx[pos] = j;
                C->values[pos]  = acc[j];
                pos++;
            }
            acc[j] = 0.0f;
        }
    }

    free(acc); free(marker); free(row_nnz); free(out_rowptr);
    return C;
}

// ---------------------------------------------------------------------------
// GPU SpGEMM kernels
// ---------------------------------------------------------------------------

// Phase 1: Count non-zeros per row of C = A * B
// BUG 1: This counts symbolic non-zeros (unique column indices that appear)
//         but does NOT account for numeric cancellation. If A[i,k1]*B[k1,j]
//         and A[i,k2]*B[k2,j] sum to zero, this still counts column j.
__global__ void spgemm_count_kernel(const int *A_rowptr, const int *A_colidx,
                                      const int *B_rowptr, const int *B_colidx,
                                      int *C_row_nnz, int M) {
    int row = blockIdx.x * blockDim.x + threadIdx.x;
    if (row >= M) return;

    // Use a simple flag array approach — count unique columns
    // BUG: this counts structural non-zeros, not numeric non-zeros
    int count = 0;
    for (int jj = A_rowptr[row]; jj < A_rowptr[row+1]; jj++) {
        int k = A_colidx[jj];
        int b_start = B_rowptr[k];
        int b_end   = B_rowptr[k+1];
        count += (b_end - b_start);  // BUG: doesn't deduplicate columns!
    }
    C_row_nnz[row] = count;
}

// Phase 2: Fill values of C = A * B
// BUG 2: Column merging uses naive O(nnz^2) approach that doesn't properly
//         accumulate values for duplicate column indices. When the same output
//         column appears from different intermediate products, it writes
//         multiple entries instead of summing them.
__global__ void spgemm_fill_kernel(const int *A_rowptr, const int *A_colidx,
                                     const float *A_values,
                                     const int *B_rowptr, const int *B_colidx,
                                     const float *B_values,
                                     int *C_rowptr, int *C_colidx, float *C_values,
                                     int M) {
    int row = blockIdx.x * blockDim.x + threadIdx.x;
    if (row >= M) return;

    int out_pos = C_rowptr[row];

    // BUG: Simply appends all products without merging duplicate columns
    // This means if A[i,k1]*B[k1,j] and A[i,k2]*B[k2,j] both contribute
    // to C[i,j], we get TWO entries for column j instead of one summed entry.
    for (int jj = A_rowptr[row]; jj < A_rowptr[row+1]; jj++) {
        int k = A_colidx[jj];
        float a_val = A_values[jj];

        for (int kk = B_rowptr[k]; kk < B_rowptr[k+1]; kk++) {
            int j = B_colidx[kk];
            float val = a_val * B_values[kk];

            C_colidx[out_pos] = j;
            C_values[out_pos] = val;
            out_pos++;
        }
    }
}

// ---------------------------------------------------------------------------
// GPU SpGEMM driver
// ---------------------------------------------------------------------------
CSRMatrix* gpu_spgemm(const CSRMatrix *h_A, const CSRMatrix *h_B) {
    int M = h_A->rows;
    int N = h_B->cols;

    // Upload A
    int *d_A_rowptr, *d_A_colidx;
    float *d_A_values;
    cudaMalloc(&d_A_rowptr, (M+1) * sizeof(int));
    cudaMalloc(&d_A_colidx, h_A->nnz * sizeof(int));
    cudaMalloc(&d_A_values, h_A->nnz * sizeof(float));
    cudaMemcpy(d_A_rowptr, h_A->row_ptr, (M+1) * sizeof(int), cudaMemcpyHostToDevice);
    cudaMemcpy(d_A_colidx, h_A->col_idx, h_A->nnz * sizeof(int), cudaMemcpyHostToDevice);
    cudaMemcpy(d_A_values, h_A->values, h_A->nnz * sizeof(float), cudaMemcpyHostToDevice);

    // Upload B
    int K = h_B->rows;
    int *d_B_rowptr, *d_B_colidx;
    float *d_B_values;
    cudaMalloc(&d_B_rowptr, (K+1) * sizeof(int));
    cudaMalloc(&d_B_colidx, h_B->nnz * sizeof(int));
    cudaMalloc(&d_B_values, h_B->nnz * sizeof(float));
    cudaMemcpy(d_B_rowptr, h_B->row_ptr, (K+1) * sizeof(int), cudaMemcpyHostToDevice);
    cudaMemcpy(d_B_colidx, h_B->col_idx, h_B->nnz * sizeof(int), cudaMemcpyHostToDevice);
    cudaMemcpy(d_B_values, h_B->values, h_B->nnz * sizeof(float), cudaMemcpyHostToDevice);

    // Phase 1: Count
    int *d_C_row_nnz;
    cudaMalloc(&d_C_row_nnz, M * sizeof(int));
    int blocks = (M + BLOCK_SIZE - 1) / BLOCK_SIZE;
    spgemm_count_kernel<<<blocks, BLOCK_SIZE>>>(
        d_A_rowptr, d_A_colidx, d_B_rowptr, d_B_colidx, d_C_row_nnz, M);

    int *h_C_row_nnz = (int *)malloc(M * sizeof(int));
    cudaMemcpy(h_C_row_nnz, d_C_row_nnz, M * sizeof(int), cudaMemcpyDeviceToHost);

    // Build C row_ptr (prefix sum)
    int *h_C_rowptr = (int *)calloc(M + 1, sizeof(int));
    for (int i = 0; i < M; i++) {
        h_C_rowptr[i+1] = h_C_rowptr[i] + h_C_row_nnz[i];
    }
    int total_nnz = h_C_rowptr[M];

    // Allocate C
    int *d_C_rowptr, *d_C_colidx;
    float *d_C_values;
    cudaMalloc(&d_C_rowptr, (M+1) * sizeof(int));
    cudaMalloc(&d_C_colidx, total_nnz * sizeof(int));
    cudaMalloc(&d_C_values, total_nnz * sizeof(float));
    cudaMemcpy(d_C_rowptr, h_C_rowptr, (M+1) * sizeof(int), cudaMemcpyHostToDevice);

    // Phase 2: Fill
    spgemm_fill_kernel<<<blocks, BLOCK_SIZE>>>(
        d_A_rowptr, d_A_colidx, d_A_values,
        d_B_rowptr, d_B_colidx, d_B_values,
        d_C_rowptr, d_C_colidx, d_C_values, M);

    // Download C
    CSRMatrix *C = csr_alloc(M, N, total_nnz);
    cudaMemcpy(C->row_ptr, h_C_rowptr, (M+1) * sizeof(int), cudaMemcpyHostToHost);
    cudaMemcpy(C->col_idx, d_C_colidx, total_nnz * sizeof(int), cudaMemcpyDeviceToHost);
    cudaMemcpy(C->values, d_C_values, total_nnz * sizeof(float), cudaMemcpyDeviceToHost);

    // Cleanup
    cudaFree(d_A_rowptr); cudaFree(d_A_colidx); cudaFree(d_A_values);
    cudaFree(d_B_rowptr); cudaFree(d_B_colidx); cudaFree(d_B_values);
    cudaFree(d_C_row_nnz); cudaFree(d_C_rowptr);
    cudaFree(d_C_colidx); cudaFree(d_C_values);
    free(h_C_row_nnz); free(h_C_rowptr);

    return C;
}

// ---------------------------------------------------------------------------
// Test matrix generators
// ---------------------------------------------------------------------------
CSRMatrix* generate_diagonal(int N) {
    CSRMatrix *m = csr_alloc(N, N, N);
    for (int i = 0; i <= N; i++) m->row_ptr[i] = i;
    for (int i = 0; i < N; i++) {
        m->col_idx[i] = i;
        m->values[i]  = 1.0f + (float)(i % 3);
    }
    return m;
}

CSRMatrix* generate_random_sparse(int rows, int cols, float density, unsigned int seed) {
    srand(seed);
    int max_nnz = (int)(rows * cols * density) + rows;
    int *tmp_col = (int *)malloc(max_nnz * sizeof(int));
    float *tmp_val = (float *)malloc(max_nnz * sizeof(float));
    int *tmp_rowptr = (int *)calloc(rows + 1, sizeof(int));

    int nnz = 0;
    for (int i = 0; i < rows; i++) {
        tmp_rowptr[i] = nnz;
        for (int j = 0; j < cols; j++) {
            if ((float)rand() / RAND_MAX < density) {
                tmp_col[nnz] = j;
                tmp_val[nnz] = ((float)rand() / RAND_MAX) * 4.0f - 2.0f;
                nnz++;
            }
        }
    }
    tmp_rowptr[rows] = nnz;

    CSRMatrix *m = csr_alloc(rows, cols, nnz);
    memcpy(m->row_ptr, tmp_rowptr, (rows+1) * sizeof(int));
    memcpy(m->col_idx, tmp_col, nnz * sizeof(int));
    memcpy(m->values, tmp_val, nnz * sizeof(float));

    free(tmp_col); free(tmp_val); free(tmp_rowptr);
    return m;
}

// Generate matrix with cancellation: some products will sum to zero
CSRMatrix* generate_cancellation_matrix(int N, unsigned int seed) {
    srand(seed);
    int max_nnz = N * 4;
    int *tmp_col = (int *)malloc(max_nnz * sizeof(int));
    float *tmp_val = (float *)malloc(max_nnz * sizeof(float));
    int *tmp_rowptr = (int *)calloc(N + 1, sizeof(int));

    int nnz = 0;
    for (int i = 0; i < N; i++) {
        tmp_rowptr[i] = nnz;
        // Each row has 2-3 entries, some with opposite signs
        int n_entries = 2 + rand() % 2;
        for (int e = 0; e < n_entries && nnz < max_nnz; e++) {
            tmp_col[nnz] = rand() % N;
            tmp_val[nnz] = (e % 2 == 0) ? 1.0f : -1.0f;
            nnz++;
        }
    }
    tmp_rowptr[N] = nnz;

    CSRMatrix *m = csr_alloc(N, N, nnz);
    memcpy(m->row_ptr, tmp_rowptr, (N+1) * sizeof(int));
    memcpy(m->col_idx, tmp_col, nnz * sizeof(int));
    memcpy(m->values, tmp_val, nnz * sizeof(float));

    free(tmp_col); free(tmp_val); free(tmp_rowptr);
    return m;
}

// ---------------------------------------------------------------------------
// Comparison
// ---------------------------------------------------------------------------
int compare_csr(const CSRMatrix *cpu_C, const CSRMatrix *gpu_C,
                int *out_value_errs, int *out_extra_zeros, int *out_dup_cols) {
    int value_errors = 0;
    int extra_zeros = 0;
    int dup_cols = 0;

    // Check for extra zeros in GPU output
    for (int i = 0; i < gpu_C->rows; i++) {
        for (int jj = gpu_C->row_ptr[i]; jj < gpu_C->row_ptr[i+1]; jj++) {
            if (fabsf(gpu_C->values[jj]) < 1e-10f) extra_zeros++;
        }
        // Check duplicate columns
        for (int jj = gpu_C->row_ptr[i]; jj < gpu_C->row_ptr[i+1]; jj++) {
            for (int kk = jj+1; kk < gpu_C->row_ptr[i+1]; kk++) {
                if (gpu_C->col_idx[jj] == gpu_C->col_idx[kk]) dup_cols++;
            }
        }
    }

    // Compare values: convert both to dense and compare
    int N = cpu_C->cols;
    float *dense_cpu = (float *)calloc(cpu_C->rows * N, sizeof(float));
    float *dense_gpu = (float *)calloc(gpu_C->rows * N, sizeof(float));

    for (int i = 0; i < cpu_C->rows; i++) {
        for (int jj = cpu_C->row_ptr[i]; jj < cpu_C->row_ptr[i+1]; jj++) {
            dense_cpu[i * N + cpu_C->col_idx[jj]] = cpu_C->values[jj];
        }
    }
    for (int i = 0; i < gpu_C->rows; i++) {
        for (int jj = gpu_C->row_ptr[i]; jj < gpu_C->row_ptr[i+1]; jj++) {
            // For duplicates, sum the values (this is what the bug produces)
            dense_gpu[i * N + gpu_C->col_idx[jj]] += gpu_C->values[jj];
        }
    }

    for (int i = 0; i < cpu_C->rows * N; i++) {
        if (fabsf(dense_cpu[i] - dense_gpu[i]) > 1e-3f) value_errors++;
    }

    *out_value_errs = value_errors;
    *out_extra_zeros = extra_zeros;
    *out_dup_cols = dup_cols;

    free(dense_cpu); free(dense_gpu);
    return (value_errors == 0 && extra_zeros == 0 && dup_cols == 0) ? 1 : 0;
}

// ---------------------------------------------------------------------------
int main(int argc, char **argv) {
    int mode = 0;  // 0=diagonal, 1=random, 2=cancellation
    int N = 32;
    float density = 0.2f;
    unsigned int seed = 42;

    for (int k = 1; k < argc; k++) {
        if (strcmp(argv[k], "--mode") == 0 && k+1 < argc) {
            if (strcmp(argv[k+1], "diagonal") == 0) mode = 0;
            else if (strcmp(argv[k+1], "random") == 0) mode = 1;
            else if (strcmp(argv[k+1], "cancel") == 0) mode = 2;
            k++;
        }
        else if (strcmp(argv[k], "--size") == 0 && k+1 < argc) N = atoi(argv[++k]);
        else if (strcmp(argv[k], "--density") == 0 && k+1 < argc) density = atof(argv[++k]);
        else if (strcmp(argv[k], "--seed") == 0 && k+1 < argc) seed = (unsigned int)atoi(argv[++k]);
    }

    CSRMatrix *A, *B;
    if (mode == 0) {
        A = generate_diagonal(N);
        B = generate_diagonal(N);
    } else if (mode == 1) {
        A = generate_random_sparse(N, N, density, seed);
        B = generate_random_sparse(N, N, density, seed + 100);
    } else {
        A = generate_cancellation_matrix(N, seed);
        B = generate_cancellation_matrix(N, seed + 200);
    }

    CSRMatrix *cpu_C = cpu_spgemm(A, B);
    CSRMatrix *gpu_C = gpu_spgemm(A, B);

    int value_errs, extra_zeros, dup_cols;
    int match = compare_csr(cpu_C, gpu_C, &value_errs, &extra_zeros, &dup_cols);

    printf("MODE=%d\n", mode);
    printf("SIZE=%d\n", N);
    printf("A_NNZ=%d\n", A->nnz);
    printf("B_NNZ=%d\n", B->nnz);
    printf("CPU_C_NNZ=%d\n", cpu_C->nnz);
    printf("GPU_C_NNZ=%d\n", gpu_C->nnz);
    printf("VALUE_ERRORS=%d\n", value_errs);
    printf("EXTRA_ZEROS=%d\n", extra_zeros);
    printf("DUP_COLS=%d\n", dup_cols);
    printf("NNZ_MATCH=%d\n", cpu_C->nnz == gpu_C->nnz ? 1 : 0);
    printf("MATCH=%d\n", match);

    csr_free(A); csr_free(B); csr_free(cpu_C); csr_free(gpu_C);
    return match ? 0 : 1;
}
