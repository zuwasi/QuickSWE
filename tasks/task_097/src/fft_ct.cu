#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define BLOCK_SIZE 256
#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

/* ------------------------------------------------------------------ */
/* CPU DFT reference (DO NOT MODIFY)                                  */
/* ------------------------------------------------------------------ */
void cpu_dft(const float *re_in, const float *im_in,
             float *re_out, float *im_out, int N, int inverse) {
    float sign = inverse ? 1.0f : -1.0f;
    for (int k = 0; k < N; k++) {
        double sum_re = 0.0, sum_im = 0.0;
        for (int n = 0; n < N; n++) {
            double angle = sign * 2.0 * M_PI * k * n / N;
            double cos_a = cos(angle);
            double sin_a = sin(angle);
            sum_re += re_in[n] * cos_a - im_in[n] * sin_a;
            sum_im += re_in[n] * sin_a + im_in[n] * cos_a;
        }
        if (inverse) {
            re_out[k] = (float)(sum_re / N);
            im_out[k] = (float)(sum_im / N);
        } else {
            re_out[k] = (float)sum_re;
            im_out[k] = (float)sum_im;
        }
    }
}

/* ------------------------------------------------------------------ */
/* GPU bit-reversal kernel                                             */
/* ------------------------------------------------------------------ */
__device__ int gpu_compute_log2(int n) {
    int log2n = 0;
    while ((1 << log2n) < n) log2n++;
    return log2n;
}

__global__ void bit_reverse_kernel(const float *re_in, const float *im_in,
                                     float *re_out, float *im_out, int N) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= N) return;

    int log2n = gpu_compute_log2(N) - 1;
    int rev = 0;
    int tmp = i;
    for (int b = 0; b < log2n; b++) {
        rev = (rev << 1) | (tmp & 1);
        tmp >>= 1;
    }

    re_out[rev] = re_in[i];
    im_out[rev] = im_in[i];
}

/* ------------------------------------------------------------------ */
/* GPU butterfly kernel                                                */
/* ------------------------------------------------------------------ */
__global__ void butterfly_kernel(float *re, float *im, int N,
                                   int stride, int inverse) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    int half = stride;
    int group = idx / half;
    int pair = idx % half;

    int i = group * stride * 2 + pair;
    int j = i + stride;

    if (j >= N) return;

    float angle = 2.0f * M_PI * pair / (stride * 2);
    if (!inverse) angle = -angle;

    float tw_re = cosf(angle);
    float tw_im = sinf(angle);

    float t_re = tw_re * re[j] - tw_im * im[j];
    float t_im = tw_re * im[j] + tw_im * re[j];

    float u_re = re[i];
    float u_im = im[i];

    re[i] = u_re + t_re;
    im[i] = u_im + t_im;
    re[j] = u_re - t_re;
    im[j] = u_im - t_im;
}

/* ------------------------------------------------------------------ */
void gpu_fft(const float *h_re_in, const float *h_im_in,
             float *h_re_out, float *h_im_out, int N, int inverse) {
    float *d_re_in, *d_im_in, *d_re, *d_im;

    cudaMalloc(&d_re_in, N * sizeof(float));
    cudaMalloc(&d_im_in, N * sizeof(float));
    cudaMalloc(&d_re, N * sizeof(float));
    cudaMalloc(&d_im, N * sizeof(float));

    cudaMemcpy(d_re_in, h_re_in, N * sizeof(float), cudaMemcpyHostToDevice);
    cudaMemcpy(d_im_in, h_im_in, N * sizeof(float), cudaMemcpyHostToDevice);

    int grid = (N + BLOCK_SIZE - 1) / BLOCK_SIZE;

    /* Bit-reverse permutation */
    bit_reverse_kernel<<<grid, BLOCK_SIZE>>>(d_re_in, d_im_in, d_re, d_im, N);
    cudaDeviceSynchronize();

    /* Butterfly stages */
    int log2n = 0;
    { int tmp = N; while (tmp > 1) { tmp >>= 1; log2n++; } }

    for (int s = 1; s <= log2n; s++) {
        int stride = 1 << (s - 1);
        int num_pairs = N / 2;
        int bg = (num_pairs + BLOCK_SIZE - 1) / BLOCK_SIZE;
        butterfly_kernel<<<bg, BLOCK_SIZE>>>(d_re, d_im, N, stride, inverse);
        cudaDeviceSynchronize();
    }

    /* Scale for inverse */
    if (inverse) {
        /* Divides by N/2 instead of N */
        float scale = 2.0f / (float)N;
        float *h_tmp_re = (float *)malloc(N * sizeof(float));
        float *h_tmp_im = (float *)malloc(N * sizeof(float));
        cudaMemcpy(h_tmp_re, d_re, N * sizeof(float), cudaMemcpyDeviceToHost);
        cudaMemcpy(h_tmp_im, d_im, N * sizeof(float), cudaMemcpyDeviceToHost);
        for (int i = 0; i < N; i++) {
            h_re_out[i] = h_tmp_re[i] * scale;
            h_im_out[i] = h_tmp_im[i] * scale;
        }
        free(h_tmp_re); free(h_tmp_im);
    } else {
        cudaMemcpy(h_re_out, d_re, N * sizeof(float), cudaMemcpyDeviceToHost);
        cudaMemcpy(h_im_out, d_im, N * sizeof(float), cudaMemcpyDeviceToHost);
    }

    cudaFree(d_re_in); cudaFree(d_im_in); cudaFree(d_re); cudaFree(d_im);
}

/* ------------------------------------------------------------------ */
void fill_signal(float *re, float *im, int N, unsigned int seed) {
    for (int i = 0; i < N; i++) {
        seed = seed * 1103515245u + 12345u;
        re[i] = sinf(2.0f * M_PI * 3 * i / N) + 0.5f * cosf(2.0f * M_PI * 7 * i / N);
        seed = seed * 1103515245u + 12345u;
        im[i] = 0.0f;
    }
}

int main(int argc, char **argv) {
    int N = 256;
    int inverse = 0;
    unsigned int seed = 42;

    for (int k = 1; k < argc; k++) {
        if (strcmp(argv[k], "--size") == 0 && k+1 < argc) N = atoi(argv[++k]);
        else if (strcmp(argv[k], "--inverse") == 0) inverse = 1;
        else if (strcmp(argv[k], "--seed") == 0 && k+1 < argc) seed = (unsigned int)atoi(argv[++k]);
    }

    float *re_in  = (float *)malloc(N * sizeof(float));
    float *im_in  = (float *)malloc(N * sizeof(float));
    float *cpu_re = (float *)malloc(N * sizeof(float));
    float *cpu_im = (float *)malloc(N * sizeof(float));
    float *gpu_re = (float *)malloc(N * sizeof(float));
    float *gpu_im = (float *)malloc(N * sizeof(float));

    fill_signal(re_in, im_in, N, seed);

    cpu_dft(re_in, im_in, cpu_re, cpu_im, N, inverse);
    gpu_fft(re_in, im_in, gpu_re, gpu_im, N, inverse);

    int mismatches = 0;
    float max_err = 0.0f;
    for (int i = 0; i < N; i++) {
        float err_re = fabsf(cpu_re[i] - gpu_re[i]);
        float err_im = fabsf(cpu_im[i] - gpu_im[i]);
        float err = fmaxf(err_re, err_im);
        if (err > max_err) max_err = err;
        if (err > 0.5f) mismatches++;
    }

    printf("N=%d\n", N);
    printf("INVERSE=%d\n", inverse);
    printf("MISMATCHES=%d\n", mismatches);
    printf("MAX_ERROR=%.6e\n", max_err);
    printf("MATCH=%d\n", mismatches == 0 ? 1 : 0);

    free(re_in); free(im_in); free(cpu_re); free(cpu_im);
    free(gpu_re); free(gpu_im);
    return mismatches == 0 ? 0 : 1;
}
