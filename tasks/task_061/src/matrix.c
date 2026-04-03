#include <stdio.h>
#include <string.h>
#include "matrix.h"

void mat_zero(Matrix *m, int rows, int cols) {
    m->rows = rows;
    m->cols = cols;
    memset(m->data, 0, sizeof(m->data));
}

void mat_set(Matrix *m, int r, int c, double val) {
    m->data[r][c] = val;
}

double mat_get(Matrix *m, int r, int c) {
    return m->data[r][c];
}

int mat_multiply(const Matrix *A, const Matrix *B, Matrix *C) {
    if (A->cols != B->rows) {
        return -1;  /* dimension mismatch */
    }

    C->rows = A->rows;
    C->cols = B->cols;
    memset(C->data, 0, sizeof(C->data));

    for (int i = 0; i < A->rows; i++) {
        for (int j = 0; j < B->cols; j++) {
            for (int k = 0; k < A->cols; k++) {
                /* BUG: should be C->data[i][j], not C->data[i][k] */
                C->data[i][k] += A->data[i][k] * B->data[k][j];
            }
        }
    }

    return 0;
}

void mat_print(const Matrix *m) {
    for (int i = 0; i < m->rows; i++) {
        for (int j = 0; j < m->cols; j++) {
            if (j > 0) printf(" ");
            if (m->data[i][j] == (int)m->data[i][j]) {
                printf("%d", (int)m->data[i][j]);
            } else {
                printf("%.2f", m->data[i][j]);
            }
        }
        printf("\n");
    }
}
