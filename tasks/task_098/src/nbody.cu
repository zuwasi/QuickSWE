#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define BLOCK_SIZE 128
#define SOFTENING 0.01f
#define DT 0.001f

/* ------------------------------------------------------------------ */
/* CPU N-body reference (DO NOT MODIFY)                               */
/* ------------------------------------------------------------------ */
void cpu_nbody_step(float *px, float *py, float *pz,
                     float *vx, float *vy, float *vz,
                     const float *mass, int N) {
    float *ax = (float *)calloc(N, sizeof(float));
    float *ay = (float *)calloc(N, sizeof(float));
    float *az = (float *)calloc(N, sizeof(float));

    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            if (i == j) continue;
            float dx = px[j] - px[i];
            float dy = py[j] - py[i];
            float dz = pz[j] - pz[i];
            float r2 = dx * dx + dy * dy + dz * dz + SOFTENING * SOFTENING;
            float r = sqrtf(r2);
            float f = mass[j] / (r2 * r);
            ax[i] += f * dx;
            ay[i] += f * dy;
            az[i] += f * dz;
        }
    }

    for (int i = 0; i < N; i++) {
        vx[i] += ax[i] * DT;
        vy[i] += ay[i] * DT;
        vz[i] += az[i] * DT;
        px[i] += vx[i] * DT;
        py[i] += vy[i] * DT;
        pz[i] += vz[i] * DT;
    }

    free(ax); free(ay); free(az);
}

/* ------------------------------------------------------------------ */
/* GPU kernel                                                          */
/* ------------------------------------------------------------------ */
__global__ void nbody_force_kernel(const float *px, const float *py,
                                     const float *pz, const float *mass,
                                     float *ax, float *ay, float *az,
                                     int N) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= N) return;

    float xi = px[i], yi = py[i], zi = pz[i];
    float fax = 0.0f, fay = 0.0f, faz = 0.0f;

    for (int j = 0; j < N; j++) {
        if (j == i) continue;
        float dx = px[j] - xi;
        float dy = py[j] - yi;
        float dz = pz[j] - zi;
        float r2 = dx * dx + dy * dy + dz * dz + SOFTENING;
        float f = mass[j] / (r2);
        fax += f * dx;
        fay += f * dy;
        faz += f * dz;
    }

    ax[i] = fax;
    ay[i] = fay;
    az[i] = faz;
}

__global__ void nbody_integrate_kernel(float *px, float *py, float *pz,
                                         float *vx, float *vy, float *vz,
                                         const float *ax, const float *ay,
                                         const float *az, int N, float dt) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= N) return;

    px[i] += vx[i] * dt;
    py[i] += vy[i] * dt;
    pz[i] += vz[i] * dt;

    vx[i] += ax[i] * dt;
    vy[i] += ay[i] * dt;
    vz[i] += az[i] * dt;
}

/* ------------------------------------------------------------------ */
void gpu_nbody_step(float *h_px, float *h_py, float *h_pz,
                     float *h_vx, float *h_vy, float *h_vz,
                     const float *h_mass, int N) {
    float *d_px, *d_py, *d_pz, *d_vx, *d_vy, *d_vz;
    float *d_ax, *d_ay, *d_az, *d_mass;

    cudaMalloc(&d_px, N * sizeof(float)); cudaMalloc(&d_py, N * sizeof(float));
    cudaMalloc(&d_pz, N * sizeof(float));
    cudaMalloc(&d_vx, N * sizeof(float)); cudaMalloc(&d_vy, N * sizeof(float));
    cudaMalloc(&d_vz, N * sizeof(float));
    cudaMalloc(&d_ax, N * sizeof(float)); cudaMalloc(&d_ay, N * sizeof(float));
    cudaMalloc(&d_az, N * sizeof(float));
    cudaMalloc(&d_mass, N * sizeof(float));

    cudaMemcpy(d_px, h_px, N * sizeof(float), cudaMemcpyHostToDevice);
    cudaMemcpy(d_py, h_py, N * sizeof(float), cudaMemcpyHostToDevice);
    cudaMemcpy(d_pz, h_pz, N * sizeof(float), cudaMemcpyHostToDevice);
    cudaMemcpy(d_vx, h_vx, N * sizeof(float), cudaMemcpyHostToDevice);
    cudaMemcpy(d_vy, h_vy, N * sizeof(float), cudaMemcpyHostToDevice);
    cudaMemcpy(d_vz, h_vz, N * sizeof(float), cudaMemcpyHostToDevice);
    cudaMemcpy(d_mass, h_mass, N * sizeof(float), cudaMemcpyHostToDevice);

    int grid = (N + BLOCK_SIZE - 1) / BLOCK_SIZE;

    nbody_force_kernel<<<grid, BLOCK_SIZE>>>(d_px, d_py, d_pz, d_mass,
                                               d_ax, d_ay, d_az, N);
    cudaDeviceSynchronize();

    nbody_integrate_kernel<<<grid, BLOCK_SIZE>>>(d_px, d_py, d_pz,
                                                    d_vx, d_vy, d_vz,
                                                    d_ax, d_ay, d_az, N, DT);
    cudaDeviceSynchronize();

    cudaMemcpy(h_px, d_px, N * sizeof(float), cudaMemcpyDeviceToHost);
    cudaMemcpy(h_py, d_py, N * sizeof(float), cudaMemcpyDeviceToHost);
    cudaMemcpy(h_pz, d_pz, N * sizeof(float), cudaMemcpyDeviceToHost);
    cudaMemcpy(h_vx, d_vx, N * sizeof(float), cudaMemcpyDeviceToHost);
    cudaMemcpy(h_vy, d_vy, N * sizeof(float), cudaMemcpyDeviceToHost);
    cudaMemcpy(h_vz, d_vz, N * sizeof(float), cudaMemcpyDeviceToHost);

    cudaFree(d_px); cudaFree(d_py); cudaFree(d_pz);
    cudaFree(d_vx); cudaFree(d_vy); cudaFree(d_vz);
    cudaFree(d_ax); cudaFree(d_ay); cudaFree(d_az);
    cudaFree(d_mass);
}

/* ------------------------------------------------------------------ */
void init_bodies(float *px, float *py, float *pz,
                  float *vx, float *vy, float *vz,
                  float *mass, int N, unsigned int seed) {
    for (int i = 0; i < N; i++) {
        seed = seed * 1103515245u + 12345u;
        px[i] = (float)(seed % 10000) / 1000.0f - 5.0f;
        seed = seed * 1103515245u + 12345u;
        py[i] = (float)(seed % 10000) / 1000.0f - 5.0f;
        seed = seed * 1103515245u + 12345u;
        pz[i] = (float)(seed % 10000) / 1000.0f - 5.0f;
        vx[i] = vy[i] = vz[i] = 0.0f;
        seed = seed * 1103515245u + 12345u;
        mass[i] = 0.1f + (float)(seed % 100) / 100.0f;
    }
}

int main(int argc, char **argv) {
    int N = 128;
    int steps = 5;
    unsigned int seed = 42;

    for (int k = 1; k < argc; k++) {
        if (strcmp(argv[k], "--size") == 0 && k+1 < argc) N = atoi(argv[++k]);
        else if (strcmp(argv[k], "--steps") == 0 && k+1 < argc) steps = atoi(argv[++k]);
        else if (strcmp(argv[k], "--seed") == 0 && k+1 < argc) seed = (unsigned int)atoi(argv[++k]);
    }

    size_t sz = N * sizeof(float);
    float *cpu_px = (float*)malloc(sz), *cpu_py = (float*)malloc(sz), *cpu_pz = (float*)malloc(sz);
    float *cpu_vx = (float*)malloc(sz), *cpu_vy = (float*)malloc(sz), *cpu_vz = (float*)malloc(sz);
    float *gpu_px = (float*)malloc(sz), *gpu_py = (float*)malloc(sz), *gpu_pz = (float*)malloc(sz);
    float *gpu_vx = (float*)malloc(sz), *gpu_vy = (float*)malloc(sz), *gpu_vz = (float*)malloc(sz);
    float *mass = (float*)malloc(sz);

    init_bodies(cpu_px, cpu_py, cpu_pz, cpu_vx, cpu_vy, cpu_vz, mass, N, seed);
    memcpy(gpu_px, cpu_px, sz); memcpy(gpu_py, cpu_py, sz); memcpy(gpu_pz, cpu_pz, sz);
    memcpy(gpu_vx, cpu_vx, sz); memcpy(gpu_vy, cpu_vy, sz); memcpy(gpu_vz, cpu_vz, sz);

    for (int s = 0; s < steps; s++) {
        cpu_nbody_step(cpu_px, cpu_py, cpu_pz, cpu_vx, cpu_vy, cpu_vz, mass, N);
        gpu_nbody_step(gpu_px, gpu_py, gpu_pz, gpu_vx, gpu_vy, gpu_vz, mass, N);
    }

    int mismatches = 0;
    float max_err = 0.0f;
    for (int i = 0; i < N; i++) {
        float err = fabsf(cpu_px[i] - gpu_px[i]) + fabsf(cpu_py[i] - gpu_py[i]) +
                    fabsf(cpu_pz[i] - gpu_pz[i]);
        if (err > max_err) max_err = err;
        if (err > 0.01f) mismatches++;
    }

    printf("N=%d\n", N);
    printf("STEPS=%d\n", steps);
    printf("MISMATCHES=%d\n", mismatches);
    printf("MAX_ERROR=%.6e\n", max_err);
    printf("MATCH=%d\n", mismatches == 0 ? 1 : 0);

    free(cpu_px); free(cpu_py); free(cpu_pz);
    free(cpu_vx); free(cpu_vy); free(cpu_vz);
    free(gpu_px); free(gpu_py); free(gpu_pz);
    free(gpu_vx); free(gpu_vy); free(gpu_vz);
    free(mass);
    return mismatches == 0 ? 0 : 1;
}
