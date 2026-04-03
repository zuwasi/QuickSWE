#ifndef MATRIX_H
#define MATRIX_H

#define MAX_DIM 10

typedef struct {
    int rows;
    int cols;
    double data[MAX_DIM][MAX_DIM];
} Matrix;

void mat_zero(Matrix *m, int rows, int cols);
void mat_set(Matrix *m, int r, int c, double val);
double mat_get(Matrix *m, int r, int c);
int mat_multiply(const Matrix *A, const Matrix *B, Matrix *C);
void mat_print(const Matrix *m);

#endif
