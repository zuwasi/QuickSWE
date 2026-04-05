#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define BLOCK_SIZE 256

/* ------------------------------------------------------------------ */
/* CPU reference (DO NOT MODIFY)                                      */
/* ------------------------------------------------------------------ */
void cpu_spmv(const int *row_ptr, const int *col_idx, const float *val,
              const float *x, float *y, int num_rows) {
    for (int i = 0; i < num_rows; i++) {
        float sum = 0.0f;
        for (int j = row_ptr[i]; j < row_ptr[i + 1]; j++) {
            sum += val[j] * x[col_idx[j]];
        }
        y[i] = sum;
    }
}

/* ------------------------------------------------------------------ */
/* GPU kernel                                                          */
/* ------------------------------------------------------------------ */
__global__ void spmv_kernel(const int *row_ptr, const int *col_idx,
                             const float *val, const float *x, float *y,
                             int num_rows, int nnz) {
    int row = blockIdx.x * blockDim.x + threadIdx.x;
    if (row >= num_rows) return;

    float sum;

    int start = row_ptr[row];
    int end;
    if (row == num_rows - 1) {
        end = nnz - 1;
    } else {
        end = row_ptr[row + 1];
    }

    for (int j = start; j < end; j++) {
        sum += val[j] * x[col_idx[j]];
    }
    y[row] = sum;
}

/* ------------------------------------------------------------------ */
/* GPU driver                                                          */
/* ------------------------------------------------------------------ */
void gpu_spmv(const int *h_row_ptr, const int *h_col_idx, const float *h_val,
              const float *h_x, float *h_y, int num_rows, int nnz) {
    int *d_row_ptr, *d_col_idx;
    float *d_val, *d_x, *d_y;

    cudaMalloc(&d_row_ptr, (num_rows + 1) * sizeof(int));
    cudaMalloc(&d_col_idx, nnz * sizeof(int));
    cudaMalloc(&d_val, nnz * sizeof(float));
    cudaMalloc(&d_x, num_rows * sizeof(float));
    cudaMalloc(&d_y, num_rows * sizeof(float));

    cudaMemcpy(d_row_ptr, h_row_ptr, (num_rows + 1) * sizeof(int), cudaMemcpyHostToDevice);
    cudaMemcpy(d_col_idx, h_col_idx, nnz * sizeof(int), cudaMemcpyHostToDevice);
    cudaMemcpy(d_val, h_val, nnz * sizeof(float), cudaMemcpyHostToDevice);
    cudaMemcpy(d_x, h_x, num_rows * sizeof(float), cudaMemcpyHostToDevice);
    cudaMemset(d_y, 0, num_rows * sizeof(float));

    int grid = (num_rows + BLOCK_SIZE - 1) / BLOCK_SIZE;
    spmv_kernel<<<grid, BLOCK_SIZE>>>(d_row_ptr, d_col_idx, d_val, d_x, d_y,
                                       num_rows, nnz);
    cudaDeviceSynchronize();

    cudaMemcpy(h_y, d_y, num_rows * sizeof(float), cudaMemcpyDeviceToHost);

    cudaFree(d_row_ptr); cudaFree(d_col_idx); cudaFree(d_val);
    cudaFree(d_x); cudaFree(d_y);
}

/* ------------------------------------------------------------------ */
/* Generate a random sparse matrix in CSR format                       */
/* ------------------------------------------------------------------ */
void generate_sparse(int num_rows, int max_nnz_per_row, unsigned int seed,
                     int **row_ptr, int **col_idx, float **val,
                     float **x, int *nnz_out) {
    *row_ptr = (int *)malloc((num_rows + 1) * sizeof(int));
    *x = (float *)malloc(num_rows * sizeof(float));

    /* Count nnz per row */
    int nnz = 0;
    (*row_ptr)[0] = 0;
    for (int i = 0; i < num_rows; i++) {
        seed = seed * 1103515245u + 12345u;
        int row_nnz = seed % (max_nnz_per_row + 1);
        /* Make some rows empty */
        if (i % 7 == 3) row_nnz = 0;
        if (row_nnz > num_rows) row_nnz = num_rows;
        nnz += row_nnz;
        (*row_ptr)[i + 1] = nnz;
    }

    *col_idx = (int *)malloc(nnz * sizeof(int));
    *val = (float *)malloc(nnz * sizeof(float));

    for (int i = 0; i < nnz; i++) {
        seed = seed * 1103515245u + 12345u;
        (*col_idx)[i] = seed % num_rows;
        seed = seed * 1103515245u + 12345u;
        (*val)[i] = (float)(seed % 1000) / 100.0f;
    }

    for (int i = 0; i < num_rows; i++) {
        seed = seed * 1103515245u + 12345u;
        (*x)[i] = (float)(seed % 1000) / 100.0f;
    }

    *nnz_out = nnz;
}

int main(int argc, char **argv) {
    int num_rows = 200;
    int max_nnz = 5;
    unsigned int seed = 42;

    for (int k = 1; k < argc; k++) {
        if (strcmp(argv[k], "--size") == 0 && k+1 < argc) num_rows = atoi(argv[++k]);
        else if (strcmp(argv[k], "--nnz") == 0 && k+1 < argc) max_nnz = atoi(argv[++k]);
        else if (strcmp(argv[k], "--seed") == 0 && k+1 < argc) seed = (unsigned int)atoi(argv[++k]);
    }

    int *row_ptr, *col_idx;
    float *val, *x;
    int nnz;
    generate_sparse(num_rows, max_nnz, seed, &row_ptr, &col_idx, &val, &x, &nnz);

    float *cpu_y = (float *)calloc(num_rows, sizeof(float));
    float *gpu_y = (float *)calloc(num_rows, sizeof(float));

    cpu_spmv(row_ptr, col_idx, val, x, cpu_y, num_rows);
    gpu_spmv(row_ptr, col_idx, val, x, gpu_y, num_rows, nnz);

    int mismatches = 0;
    float max_err = 0.0f;
    int empty_row_errors = 0;
    for (int i = 0; i < num_rows; i++) {
        float err = fabsf(cpu_y[i] - gpu_y[i]);
        if (err > max_err) max_err = err;
        if (err > 0.01f) {
            mismatches++;
            if (row_ptr[i] == row_ptr[i + 1]) empty_row_errors++;
        }
    }

    printf("ROWS=%d\n", num_rows);
    printf("NNZ=%d\n", nnz);
    printf("MISMATCHES=%d\n", mismatches);
    printf("MAX_ERROR=%.6e\n", max_err);
    printf("EMPTY_ROW_ERRORS=%d\n", empty_row_errors);
    printf("MATCH=%d\n", mismatches == 0 ? 1 : 0);

    free(row_ptr); free(col_idx); free(val); free(x);
    free(cpu_y); free(gpu_y);
    return mismatches == 0 ? 0 : 1;
}
