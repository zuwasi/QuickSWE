#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define BLOCK_SIZE 128
#define MAX_NEIGHBORS 64
#define EPSILON 1.0f
#define SIGMA 1.0f

/* ------------------------------------------------------------------ */
/* CPU reference LJ force calculation (DO NOT MODIFY)                 */
/* ------------------------------------------------------------------ */
void cpu_lj_forces(const float *px, const float *py, const float *pz,
                    float *fx, float *fy, float *fz,
                    int N, float cutoff) {
    float cutoff2 = cutoff * cutoff;

    for (int i = 0; i < N; i++) {
        fx[i] = fy[i] = fz[i] = 0.0f;
    }

    for (int i = 0; i < N; i++) {
        for (int j = i + 1; j < N; j++) {
            float dx = px[j] - px[i];
            float dy = py[j] - py[i];
            float dz = pz[j] - pz[i];
            float r2 = dx * dx + dy * dy + dz * dz;

            if (r2 < cutoff2 && r2 > 1e-10f) {
                float r2_inv = 1.0f / r2;
                float sigma_r2 = SIGMA * SIGMA * r2_inv;
                float sigma_r6 = sigma_r2 * sigma_r2 * sigma_r2;
                float sigma_r12 = sigma_r6 * sigma_r6;
                float f_mag = 24.0f * EPSILON * r2_inv * (2.0f * sigma_r12 - sigma_r6);

                fx[i] += f_mag * dx;
                fy[i] += f_mag * dy;
                fz[i] += f_mag * dz;
                fx[j] -= f_mag * dx;
                fy[j] -= f_mag * dy;
                fz[j] -= f_mag * dz;
            }
        }
    }
}

/* ------------------------------------------------------------------ */
/* GPU neighbor list builder                                           */
/* ------------------------------------------------------------------ */
__global__ void build_neighbor_list(const float *px, const float *py,
                                      const float *pz, int *neighbors,
                                      int *num_neighbors, int N, float cutoff) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= N) return;

    float xi = px[i], yi = py[i], zi = pz[i];
    int count = 0;
    float cutoff_check = cutoff;

    for (int j = 0; j < N; j++) {
        float dx = px[j] - xi;
        float dy = py[j] - yi;
        float dz = pz[j] - zi;
        float r = dx * dx + dy * dy + dz * dz;

        if (r < cutoff_check && count < MAX_NEIGHBORS) {
            neighbors[i * MAX_NEIGHBORS + count] = j;
            count++;
        }
    }

    num_neighbors[i] = count;
}

/* ------------------------------------------------------------------ */
/* GPU LJ force kernel                                                 */
/* ------------------------------------------------------------------ */
__global__ void lj_force_kernel(const float *px, const float *py,
                                  const float *pz, const int *neighbors,
                                  const int *num_neighbors,
                                  float *fx, float *fy, float *fz,
                                  int N) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= N) return;

    float xi = px[i], yi = py[i], zi = pz[i];
    float fxi = 0.0f, fyi = 0.0f, fzi = 0.0f;

    int nn = num_neighbors[i];
    for (int n = 0; n < nn; n++) {
        int j = neighbors[i * MAX_NEIGHBORS + n];

        float dx = px[j] - xi;
        float dy = py[j] - yi;
        float dz = pz[j] - zi;
        float r2 = dx * dx + dy * dy + dz * dz;

        if (r2 > 1e-10f) {
            float r2_inv = 1.0f / r2;
            float sigma_r2 = SIGMA * SIGMA * r2_inv;
            float sigma_r6 = sigma_r2 * sigma_r2 * sigma_r2;
            float f_mag = 24.0f * EPSILON * r2_inv * (2.0f * sigma_r6 - sigma_r6);

            fxi += f_mag * dx;
            fyi += f_mag * dy;
            fzi += f_mag * dz;
        }
    }

    fx[i] = fxi;
    fy[i] = fyi;
    fz[i] = fzi;
}

/* ------------------------------------------------------------------ */
void gpu_lj_forces(const float *h_px, const float *h_py, const float *h_pz,
                    float *h_fx, float *h_fy, float *h_fz,
                    int N, float cutoff) {
    float *d_px, *d_py, *d_pz, *d_fx, *d_fy, *d_fz;
    int *d_neighbors, *d_num_neighbors;

    cudaMalloc(&d_px, N * sizeof(float));
    cudaMalloc(&d_py, N * sizeof(float));
    cudaMalloc(&d_pz, N * sizeof(float));
    cudaMalloc(&d_fx, N * sizeof(float));
    cudaMalloc(&d_fy, N * sizeof(float));
    cudaMalloc(&d_fz, N * sizeof(float));
    cudaMalloc(&d_neighbors, N * MAX_NEIGHBORS * sizeof(int));
    cudaMalloc(&d_num_neighbors, N * sizeof(int));

    cudaMemcpy(d_px, h_px, N * sizeof(float), cudaMemcpyHostToDevice);
    cudaMemcpy(d_py, h_py, N * sizeof(float), cudaMemcpyHostToDevice);
    cudaMemcpy(d_pz, h_pz, N * sizeof(float), cudaMemcpyHostToDevice);
    cudaMemset(d_fx, 0, N * sizeof(float));
    cudaMemset(d_fy, 0, N * sizeof(float));
    cudaMemset(d_fz, 0, N * sizeof(float));

    int grid = (N + BLOCK_SIZE - 1) / BLOCK_SIZE;

    build_neighbor_list<<<grid, BLOCK_SIZE>>>(d_px, d_py, d_pz,
        d_neighbors, d_num_neighbors, N, cutoff);
    cudaDeviceSynchronize();

    lj_force_kernel<<<grid, BLOCK_SIZE>>>(d_px, d_py, d_pz,
        d_neighbors, d_num_neighbors, d_fx, d_fy, d_fz, N);
    cudaDeviceSynchronize();

    cudaMemcpy(h_fx, d_fx, N * sizeof(float), cudaMemcpyDeviceToHost);
    cudaMemcpy(h_fy, d_fy, N * sizeof(float), cudaMemcpyDeviceToHost);
    cudaMemcpy(h_fz, d_fz, N * sizeof(float), cudaMemcpyDeviceToHost);

    cudaFree(d_px); cudaFree(d_py); cudaFree(d_pz);
    cudaFree(d_fx); cudaFree(d_fy); cudaFree(d_fz);
    cudaFree(d_neighbors); cudaFree(d_num_neighbors);
}

/* ------------------------------------------------------------------ */
void init_positions(float *px, float *py, float *pz, int N,
                     unsigned int seed) {
    /* Place particles on a grid with some jitter */
    int side = (int)ceilf(cbrtf((float)N));
    float spacing = 1.5f * SIGMA;
    int idx = 0;
    for (int x = 0; x < side && idx < N; x++)
        for (int y = 0; y < side && idx < N; y++)
            for (int z = 0; z < side && idx < N; z++) {
                seed = seed * 1103515245u + 12345u;
                px[idx] = x * spacing + (float)(seed % 100) / 1000.0f;
                seed = seed * 1103515245u + 12345u;
                py[idx] = y * spacing + (float)(seed % 100) / 1000.0f;
                seed = seed * 1103515245u + 12345u;
                pz[idx] = z * spacing + (float)(seed % 100) / 1000.0f;
                idx++;
            }
}

int main(int argc, char **argv) {
    int N = 64;
    float cutoff = 3.0f * SIGMA;
    unsigned int seed = 42;

    for (int k = 1; k < argc; k++) {
        if (strcmp(argv[k], "--size") == 0 && k+1 < argc) N = atoi(argv[++k]);
        else if (strcmp(argv[k], "--cutoff") == 0 && k+1 < argc) cutoff = atof(argv[++k]);
        else if (strcmp(argv[k], "--seed") == 0 && k+1 < argc) seed = (unsigned int)atoi(argv[++k]);
    }

    float *px = (float*)malloc(N*sizeof(float));
    float *py = (float*)malloc(N*sizeof(float));
    float *pz = (float*)malloc(N*sizeof(float));
    float *cpu_fx = (float*)calloc(N, sizeof(float));
    float *cpu_fy = (float*)calloc(N, sizeof(float));
    float *cpu_fz = (float*)calloc(N, sizeof(float));
    float *gpu_fx = (float*)calloc(N, sizeof(float));
    float *gpu_fy = (float*)calloc(N, sizeof(float));
    float *gpu_fz = (float*)calloc(N, sizeof(float));

    init_positions(px, py, pz, N, seed);
    cpu_lj_forces(px, py, pz, cpu_fx, cpu_fy, cpu_fz, N, cutoff);
    gpu_lj_forces(px, py, pz, gpu_fx, gpu_fy, gpu_fz, N, cutoff);

    int mismatches = 0;
    float max_err = 0.0f;
    int nan_count = 0;
    for (int i = 0; i < N; i++) {
        if (isnan(gpu_fx[i]) || isnan(gpu_fy[i]) || isnan(gpu_fz[i])) {
            nan_count++;
            mismatches++;
            continue;
        }
        float err = fabsf(cpu_fx[i] - gpu_fx[i]) +
                    fabsf(cpu_fy[i] - gpu_fy[i]) +
                    fabsf(cpu_fz[i] - gpu_fz[i]);
        if (err > max_err) max_err = err;
        float mag = fabsf(cpu_fx[i]) + fabsf(cpu_fy[i]) + fabsf(cpu_fz[i]) + 1e-10f;
        if (err / mag > 0.05f) mismatches++;
    }

    /* Check momentum conservation */
    float cpu_mom_x = 0, cpu_mom_y = 0, cpu_mom_z = 0;
    float gpu_mom_x = 0, gpu_mom_y = 0, gpu_mom_z = 0;
    for (int i = 0; i < N; i++) {
        cpu_mom_x += cpu_fx[i]; cpu_mom_y += cpu_fy[i]; cpu_mom_z += cpu_fz[i];
        gpu_mom_x += gpu_fx[i]; gpu_mom_y += gpu_fy[i]; gpu_mom_z += gpu_fz[i];
    }
    float cpu_mom = fabsf(cpu_mom_x) + fabsf(cpu_mom_y) + fabsf(cpu_mom_z);
    float gpu_mom = fabsf(gpu_mom_x) + fabsf(gpu_mom_y) + fabsf(gpu_mom_z);

    printf("N=%d\n", N);
    printf("CUTOFF=%.2f\n", cutoff);
    printf("MISMATCHES=%d\n", mismatches);
    printf("MAX_ERROR=%.6e\n", max_err);
    printf("NAN_COUNT=%d\n", nan_count);
    printf("CPU_MOMENTUM=%.6e\n", cpu_mom);
    printf("GPU_MOMENTUM=%.6e\n", gpu_mom);
    printf("MATCH=%d\n", mismatches == 0 ? 1 : 0);

    free(px); free(py); free(pz);
    free(cpu_fx); free(cpu_fy); free(cpu_fz);
    free(gpu_fx); free(gpu_fy); free(gpu_fz);
    return mismatches == 0 ? 0 : 1;
}
