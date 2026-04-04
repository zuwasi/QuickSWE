#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

#define BLOCK_SIZE 256

// ---------------------------------------------------------------------------
// Complex arithmetic helpers
// ---------------------------------------------------------------------------
typedef struct { float re, im; } Complex;

__host__ __device__ Complex make_complex(float re, float im) {
    Complex c; c.re = re; c.im = im; return c;
}

__host__ __device__ Complex complex_add(Complex a, Complex b) {
    return make_complex(a.re + b.re, a.im + b.im);
}

__host__ __device__ Complex complex_sub(Complex a, Complex b) {
    return make_complex(a.re - b.re, a.im - b.im);
}

__host__ __device__ Complex complex_mul(Complex a, Complex b) {
    return make_complex(a.re*b.re - a.im*b.im, a.re*b.im + a.im*b.re);
}

// ---------------------------------------------------------------------------
// CPU reference FFT (DO NOT MODIFY)
// ---------------------------------------------------------------------------
static int cpu_log2(int n) {
    int r = 0;
    while ((1 << r) < n) r++;
    return r;
}

static void cpu_bit_reverse(Complex *data, int N) {
    int log2N = cpu_log2(N);
    for (int i = 0; i < N; i++) {
        int rev = 0;
        for (int b = 0; b < log2N; b++) {
            rev |= ((i >> b) & 1) << (log2N - 1 - b);
        }
        if (rev > i) {
            Complex tmp = data[i];
            data[i] = data[rev];
            data[rev] = tmp;
        }
    }
}

void cpu_fft(Complex *data, int N, int inverse) {
    cpu_bit_reverse(data, N);
    int log2N = cpu_log2(N);

    for (int s = 1; s <= log2N; s++) {
        int m = 1 << s;
        float angle = (inverse ? 1.0f : -1.0f) * 2.0f * (float)M_PI / (float)m;
        Complex wm = make_complex(cosf(angle), sinf(angle));

        for (int k = 0; k < N; k += m) {
            Complex w = make_complex(1.0f, 0.0f);
            for (int j = 0; j < m / 2; j++) {
                Complex t = complex_mul(w, data[k + j + m/2]);
                Complex u = data[k + j];
                data[k + j]       = complex_add(u, t);
                data[k + j + m/2] = complex_sub(u, t);
                w = complex_mul(w, wm);
            }
        }
    }

    if (inverse) {
        for (int i = 0; i < N; i++) {
            data[i].re /= N;
            data[i].im /= N;
        }
    }
}

// ---------------------------------------------------------------------------
// GPU kernels
// ---------------------------------------------------------------------------

// BUG 1: bit-reversal uses log2N-1 instead of log2N, causing off-by-one
//         in butterfly pairings for certain sizes.
__device__ int gpu_compute_log2(int n) {
    int r = 0;
    while ((1 << r) < n) r++;
    return r - 1;  // BUG: should be just r, not r-1
}

__global__ void bit_reverse_kernel(Complex *data, Complex *out, int N) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= N) return;

    int log2N = gpu_compute_log2(N);
    int rev = 0;
    for (int b = 0; b < log2N; b++) {
        rev |= ((i >> b) & 1) << (log2N - 1 - b);
    }
    out[rev] = data[i];
}

// BUG 2: twiddle factor sign is wrong for inverse FFT.
//         For forward: angle = -2*PI*j/m  (sin is negative)
//         For inverse: angle = +2*PI*j/m  (sin is positive)
//         But here, the inverse negates cos instead of negating sin,
//         which produces the wrong twiddle factor.
__global__ void butterfly_kernel(Complex *data, int N, int stage, int inverse) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    int m = 1 << stage;
    int half_m = m >> 1;

    if (idx >= N / 2) return;

    int group = idx / half_m;
    int j = idx % half_m;
    int k = group * m;

    float angle = -2.0f * (float)M_PI * (float)j / (float)m;

    // BUG: For inverse, should negate the angle (making sin positive),
    // but instead negates cos component
    Complex w;
    if (inverse) {
        w = make_complex(-cosf(angle), sinf(angle));  // WRONG: should be cos(angle), -sin(angle) or equivalently cos(-angle), sin(-angle)
    } else {
        w = make_complex(cosf(angle), sinf(angle));
    }

    Complex u = data[k + j];
    Complex t = complex_mul(w, data[k + j + half_m]);
    data[k + j]          = complex_add(u, t);
    data[k + j + half_m] = complex_sub(u, t);
}

__global__ void scale_kernel(Complex *data, int N) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= N) return;
    data[i].re /= (float)N;
    data[i].im /= (float)N;
}

// ---------------------------------------------------------------------------
// GPU FFT driver
// ---------------------------------------------------------------------------
void gpu_fft(Complex *h_data, int N, int inverse) {
    Complex *d_data, *d_tmp;
    cudaMalloc(&d_data, N * sizeof(Complex));
    cudaMalloc(&d_tmp, N * sizeof(Complex));

    cudaMemcpy(d_data, h_data, N * sizeof(Complex), cudaMemcpyHostToDevice);

    int blocks = (N + BLOCK_SIZE - 1) / BLOCK_SIZE;
    int half_blocks = (N/2 + BLOCK_SIZE - 1) / BLOCK_SIZE;

    // Bit-reverse permutation
    bit_reverse_kernel<<<blocks, BLOCK_SIZE>>>(d_data, d_tmp, N);
    cudaMemcpy(d_data, d_tmp, N * sizeof(Complex), cudaMemcpyDeviceToDevice);

    // Butterfly passes
    // BUG: uses gpu_compute_log2 which returns log2N-1, so the loop
    // misses the final stage of the FFT
    int log2N_device;
    // We compute log2N on host correctly for the loop bound,
    // but the bit-reversal kernel uses the buggy device version
    int log2N = 0;
    { int tmp = N; while (tmp > 1) { tmp >>= 1; log2N++; } }

    for (int s = 1; s <= log2N; s++) {
        butterfly_kernel<<<half_blocks, BLOCK_SIZE>>>(d_data, N, s, inverse);
        cudaDeviceSynchronize();
    }

    if (inverse) {
        scale_kernel<<<blocks, BLOCK_SIZE>>>(d_data, N);
    }

    cudaMemcpy(h_data, d_data, N * sizeof(Complex), cudaMemcpyDeviceToHost);
    cudaFree(d_data);
    cudaFree(d_tmp);
}

// ---------------------------------------------------------------------------
// Test modes
// ---------------------------------------------------------------------------
void test_roundtrip(int N, unsigned int seed) {
    Complex *original = (Complex *)malloc(N * sizeof(Complex));
    Complex *gpu_data = (Complex *)malloc(N * sizeof(Complex));
    Complex *cpu_data = (Complex *)malloc(N * sizeof(Complex));

    srand(seed);
    for (int i = 0; i < N; i++) {
        float val = ((float)rand() / RAND_MAX) * 2.0f - 1.0f;
        original[i] = make_complex(val, 0.0f);
        gpu_data[i] = original[i];
        cpu_data[i] = original[i];
    }

    // CPU roundtrip
    cpu_fft(cpu_data, N, 0);
    cpu_fft(cpu_data, N, 1);
    double cpu_rms = 0.0;
    for (int i = 0; i < N; i++) {
        double dr = cpu_data[i].re - original[i].re;
        double di = cpu_data[i].im - original[i].im;
        cpu_rms += dr*dr + di*di;
    }
    cpu_rms = sqrt(cpu_rms / N);

    // GPU roundtrip
    gpu_fft(gpu_data, N, 0);
    gpu_fft(gpu_data, N, 1);
    double gpu_rms = 0.0;
    for (int i = 0; i < N; i++) {
        double dr = gpu_data[i].re - original[i].re;
        double di = gpu_data[i].im - original[i].im;
        gpu_rms += dr*dr + di*di;
    }
    gpu_rms = sqrt(gpu_rms / N);

    printf("ROUNDTRIP_N=%d\n", N);
    printf("CPU_RMS=%.6e\n", cpu_rms);
    printf("GPU_RMS=%.6e\n", gpu_rms);
    printf("ROUNDTRIP_OK=%d\n", gpu_rms < 1e-4 ? 1 : 0);

    free(original); free(gpu_data); free(cpu_data);
}

void test_sine_spike(int N, int freq) {
    Complex *data = (Complex *)malloc(N * sizeof(Complex));
    Complex *gpu_data = (Complex *)malloc(N * sizeof(Complex));

    for (int i = 0; i < N; i++) {
        float val = sinf(2.0f * (float)M_PI * (float)freq * (float)i / (float)N);
        data[i] = make_complex(val, 0.0f);
        gpu_data[i] = data[i];
    }

    // CPU FFT
    cpu_fft(data, N, 0);
    // GPU FFT
    gpu_fft(gpu_data, N, 0);

    // Find peak bin in GPU output
    int gpu_peak = 0;
    float gpu_peak_mag = 0.0f;
    int cpu_peak = 0;
    float cpu_peak_mag = 0.0f;
    for (int i = 0; i < N; i++) {
        float gm = sqrtf(gpu_data[i].re*gpu_data[i].re + gpu_data[i].im*gpu_data[i].im);
        float cm = sqrtf(data[i].re*data[i].re + data[i].im*data[i].im);
        if (gm > gpu_peak_mag) { gpu_peak_mag = gm; gpu_peak = i; }
        if (cm > cpu_peak_mag) { cpu_peak_mag = cm; cpu_peak = i; }
    }

    // Compare magnitudes
    double mag_error = 0.0;
    for (int i = 0; i < N; i++) {
        float gm = sqrtf(gpu_data[i].re*gpu_data[i].re + gpu_data[i].im*gpu_data[i].im);
        float cm = sqrtf(data[i].re*data[i].re + data[i].im*data[i].im);
        mag_error += fabs(gm - cm);
    }
    mag_error /= N;

    printf("SINE_N=%d\n", N);
    printf("SINE_FREQ=%d\n", freq);
    printf("CPU_PEAK_BIN=%d\n", cpu_peak);
    printf("GPU_PEAK_BIN=%d\n", gpu_peak);
    printf("MAG_ERROR=%.6e\n", mag_error);
    printf("PEAK_OK=%d\n", (gpu_peak == freq || gpu_peak == N - freq) ? 1 : 0);
    printf("MAG_OK=%d\n", mag_error < 0.01 ? 1 : 0);

    free(data); free(gpu_data);
}

// ---------------------------------------------------------------------------
int main(int argc, char **argv) {
    int mode = 0;  // 0 = roundtrip, 1 = sine
    int N = 256;
    int freq = 5;
    unsigned int seed = 42;

    for (int k = 1; k < argc; k++) {
        if (strcmp(argv[k], "--mode") == 0 && k+1 < argc) {
            if (strcmp(argv[k+1], "roundtrip") == 0) mode = 0;
            else if (strcmp(argv[k+1], "sine") == 0) mode = 1;
            k++;
        }
        else if (strcmp(argv[k], "--size") == 0 && k+1 < argc) N = atoi(argv[++k]);
        else if (strcmp(argv[k], "--freq") == 0 && k+1 < argc) freq = atoi(argv[++k]);
        else if (strcmp(argv[k], "--seed") == 0 && k+1 < argc) seed = (unsigned int)atoi(argv[++k]);
    }

    if (mode == 0) {
        test_roundtrip(N, seed);
    } else {
        test_sine_spike(N, freq);
    }

    return 0;
}
