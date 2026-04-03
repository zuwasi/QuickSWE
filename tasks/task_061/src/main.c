#include <stdio.h>
#include <string.h>
#include "matrix.h"

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Usage: prog <test_name>\n");
        return 1;
    }

    const char *test = argv[1];

    if (strcmp(test, "square_diagonal") == 0) {
        /*
         * Diagonal matrix × diagonal matrix = diagonal matrix.
         * With the bug C[i][k] += A[i][k]*B[k][j]:
         *   For diagonal A and B, A[i][k] is nonzero only when i==k,
         *   and B[k][j] is nonzero only when k==j. So the only nonzero
         *   contribution is when i==k==j, i.e. C[i][i]. The bug writes
         *   to C[i][k]=C[i][i] which is the same slot. So diagonal*diagonal
         *   accidentally works even with the bug.
         */
        Matrix A, B, C;
        mat_zero(&A, 2, 2);
        mat_set(&A, 0, 0, 3); mat_set(&A, 1, 1, 5);

        mat_zero(&B, 2, 2);
        mat_set(&B, 0, 0, 2); mat_set(&B, 1, 1, 4);

        mat_multiply(&A, &B, &C);
        mat_print(&C);
        /* Expected: diag(6, 20) */
    }
    else if (strcmp(test, "rect_2x3_times_3x2") == 0) {
        /* A(2x3) * B(3x2) = C(2x2) — bug should produce wrong results */
        Matrix A, B, C;
        mat_zero(&A, 2, 3);
        mat_set(&A, 0, 0, 1); mat_set(&A, 0, 1, 2); mat_set(&A, 0, 2, 3);
        mat_set(&A, 1, 0, 4); mat_set(&A, 1, 1, 5); mat_set(&A, 1, 2, 6);

        mat_zero(&B, 3, 2);
        mat_set(&B, 0, 0, 7);  mat_set(&B, 0, 1, 8);
        mat_set(&B, 1, 0, 9);  mat_set(&B, 1, 1, 10);
        mat_set(&B, 2, 0, 11); mat_set(&B, 2, 1, 12);

        mat_multiply(&A, &B, &C);
        mat_print(&C);
        /*
         * Expected: C[0][0]=1*7+2*9+3*11=58,  C[0][1]=1*8+2*10+3*12=64
         *           C[1][0]=4*7+5*9+6*11=139, C[1][1]=4*8+5*10+6*12=154
         */
    }
    else if (strcmp(test, "rect_1x3_times_3x1") == 0) {
        /* A(1x3) * B(3x1) = C(1x1) — dot product */
        Matrix A, B, C;
        mat_zero(&A, 1, 3);
        mat_set(&A, 0, 0, 2); mat_set(&A, 0, 1, 3); mat_set(&A, 0, 2, 4);

        mat_zero(&B, 3, 1);
        mat_set(&B, 0, 0, 1); mat_set(&B, 1, 0, 2); mat_set(&B, 2, 0, 3);

        mat_multiply(&A, &B, &C);
        mat_print(&C);
        /* Expected: 2*1 + 3*2 + 4*3 = 20 */
    }
    else if (strcmp(test, "dimension_mismatch") == 0) {
        Matrix A, B, C;
        mat_zero(&A, 2, 3);
        mat_zero(&B, 2, 2);
        int rc = mat_multiply(&A, &B, &C);
        printf("rc=%d\n", rc);
    }
    else {
        printf("Unknown test: %s\n", test);
        return 1;
    }

    return 0;
}
