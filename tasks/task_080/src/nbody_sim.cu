#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <float.h>

#define BLOCK_SIZE 256
#define SOFTENING  0.5f

// ---------------------------------------------------------------------------
// Data structures
// ---------------------------------------------------------------------------
typedef struct {
    float x, y, z;
    float vx, vy, vz;
    float mass;
} Particle;

// ---------------------------------------------------------------------------
// CPU reference implementation (DO NOT MODIFY)
// ---------------------------------------------------------------------------
void cpu_compute_forces(Particle *p, float *fx, float *fy, float *fz, int N, float eps) {
    float eps2 = eps * eps;
    for (int i = 0; i < N; i++) {
        double ax = 0.0, ay = 0.0, az = 0.0;
        for (int j = 0; j < N; j++) {
            if (i == j) continue;
            float dx = p[j].x - p[i].x;
            float dy = p[j].y - p[i].y;
            float dz = p[j].z - p[i].z;
            float dist2 = dx*dx + dy*dy + dz*dz + eps2;
            float inv_dist = 1.0f / sqrtf(dist2);
            float inv_dist3 = inv_dist * inv_dist * inv_dist;
            float f = p[j].mass * inv_dist3;
            ax += f * dx;
            ay += f * dy;
            az += f * dz;
        }
        fx[i] = (float)ax;
        fy[i] = (float)ay;
        fz[i] = (float)az;
    }
}

void cpu_integrate(Particle *p, const float *fx, const float *fy, const float *fz,
                   int N, float dt) {
    for (int i = 0; i < N; i++) {
        p[i].vx += fx[i] * dt;
        p[i].vy += fy[i] * dt;
        p[i].vz += fz[i] * dt;
        p[i].x  += p[i].vx * dt;
        p[i].y  += p[i].vy * dt;
        p[i].z  += p[i].vz * dt;
    }
}

double cpu_total_energy(const Particle *p, int N, float eps) {
    double ke = 0.0;
    for (int i = 0; i < N; i++) {
        float v2 = p[i].vx*p[i].vx + p[i].vy*p[i].vy + p[i].vz*p[i].vz;
        ke += 0.5 * p[i].mass * v2;
    }
    double pe = 0.0;
    float eps2 = eps * eps;
    for (int i = 0; i < N; i++) {
        for (int j = i+1; j < N; j++) {
            float dx = p[j].x - p[i].x;
            float dy = p[j].y - p[i].y;
            float dz = p[j].z - p[i].z;
            float dist2 = dx*dx + dy*dy + dz*dz + eps2;
            float dist  = sqrtf(dist2);
            pe -= p[i].mass * p[j].mass / dist;
        }
    }
    return ke + pe;
}

// ---------------------------------------------------------------------------
// GPU kernels
// ---------------------------------------------------------------------------

// BUG 1: Softening is applied AFTER distance computation instead of inside it.
//         The eps^2 should be added to dist2 BEFORE computing inv_dist, but
//         here it's added after, which means close particles still get
//         near-infinite forces.
//
// BUG 2: Force accumulation uses float atomicAdd to a shared output buffer,
//         losing significant precision. The position update should use
//         Kahan summation or double-precision accumulation.

__global__ void compute_forces_kernel(const float *px, const float *py, const float *pz,
                                       const float *mass,
                                       float *fx, float *fy, float *fz,
                                       int N, float eps) {
    __shared__ float sh_px[BLOCK_SIZE];
    __shared__ float sh_py[BLOCK_SIZE];
    __shared__ float sh_pz[BLOCK_SIZE];
    __shared__ float sh_mass[BLOCK_SIZE];

    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= N) return;

    float xi = px[i];
    float yi = py[i];
    float zi = pz[i];

    float ax = 0.0f;
    float ay = 0.0f;
    float az = 0.0f;

    int num_tiles = (N + BLOCK_SIZE - 1) / BLOCK_SIZE;

    for (int tile = 0; tile < num_tiles; tile++) {
        int idx = tile * BLOCK_SIZE + threadIdx.x;
        if (idx < N) {
            sh_px[threadIdx.x]   = px[idx];
            sh_py[threadIdx.x]   = py[idx];
            sh_pz[threadIdx.x]   = pz[idx];
            sh_mass[threadIdx.x] = mass[idx];
        } else {
            sh_px[threadIdx.x]   = 0.0f;
            sh_py[threadIdx.x]   = 0.0f;
            sh_pz[threadIdx.x]   = 0.0f;
            sh_mass[threadIdx.x] = 0.0f;
        }
        __syncthreads();

        for (int j = 0; j < BLOCK_SIZE; j++) {
            int gj = tile * BLOCK_SIZE + j;
            if (gj >= N || gj == i) continue;

            float dx = sh_px[j] - xi;
            float dy = sh_py[j] - yi;
            float dz = sh_pz[j] - zi;

            // BUG: softening applied AFTER distance — should be dist2 = dx*dx + dy*dy + dz*dz + eps*eps
            float dist2 = dx*dx + dy*dy + dz*dz;
            float dist  = sqrtf(dist2);
            float softened_dist = dist + eps;  // WRONG: should add eps^2 to dist2
            float inv_dist3 = 1.0f / (softened_dist * softened_dist * softened_dist);

            float f = sh_mass[j] * inv_dist3;
            ax += f * dx;
            ay += f * dy;
            az += f * dz;
        }
        __syncthreads();
    }

    fx[i] = ax;
    fy[i] = ay;
    fz[i] = az;
}

// BUG 2: Integration kernel uses atomicAdd for position update through a
// shared buffer, losing precision. Should use local variable or Kahan summation.
__global__ void integrate_kernel(float *px, float *py, float *pz,
                                  float *vx, float *vy, float *vz,
                                  const float *fx, const float *fy, const float *fz,
                                  float *pos_accum_x, float *pos_accum_y, float *pos_accum_z,
                                  int N, float dt) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= N) return;

    vx[i] += fx[i] * dt;
    vy[i] += fy[i] * dt;
    vz[i] += fz[i] * dt;

    // BUG: using atomicAdd to accumulate position deltas through global buffer
    // instead of direct position update. This loses precision due to float atomics.
    atomicAdd(&pos_accum_x[i], vx[i] * dt);
    atomicAdd(&pos_accum_y[i], vy[i] * dt);
    atomicAdd(&pos_accum_z[i], vz[i] * dt);
}

__global__ void apply_positions_kernel(float *px, float *py, float *pz,
                                        const float *pos_accum_x, const float *pos_accum_y,
                                        const float *pos_accum_z, int N) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= N) return;
    px[i] += pos_accum_x[i];
    py[i] += pos_accum_y[i];
    pz[i] += pos_accum_z[i];
}

// ---------------------------------------------------------------------------
// GPU simulation driver
// ---------------------------------------------------------------------------
void gpu_nbody_step(float *d_px, float *d_py, float *d_pz,
                    float *d_vx, float *d_vy, float *d_vz,
                    float *d_mass,
                    float *d_fx, float *d_fy, float *d_fz,
                    float *d_acc_x, float *d_acc_y, float *d_acc_z,
                    int N, float dt, float eps) {
    int blocks = (N + BLOCK_SIZE - 1) / BLOCK_SIZE;

    compute_forces_kernel<<<blocks, BLOCK_SIZE>>>(
        d_px, d_py, d_pz, d_mass, d_fx, d_fy, d_fz, N, eps);

    cudaMemset(d_acc_x, 0, N * sizeof(float));
    cudaMemset(d_acc_y, 0, N * sizeof(float));
    cudaMemset(d_acc_z, 0, N * sizeof(float));

    integrate_kernel<<<blocks, BLOCK_SIZE>>>(
        d_px, d_py, d_pz, d_vx, d_vy, d_vz,
        d_fx, d_fy, d_fz, d_acc_x, d_acc_y, d_acc_z, N, dt);

    apply_positions_kernel<<<blocks, BLOCK_SIZE>>>(
        d_px, d_py, d_pz, d_acc_x, d_acc_y, d_acc_z, N);
}

// ---------------------------------------------------------------------------
// Initialization
// ---------------------------------------------------------------------------
void init_particles(Particle *p, int N, unsigned int seed) {
    srand(seed);
    for (int i = 0; i < N; i++) {
        // Particles in a cluster within [-5, 5]^3
        p[i].x = ((float)rand() / RAND_MAX) * 10.0f - 5.0f;
        p[i].y = ((float)rand() / RAND_MAX) * 10.0f - 5.0f;
        p[i].z = ((float)rand() / RAND_MAX) * 10.0f - 5.0f;
        p[i].vx = ((float)rand() / RAND_MAX) * 0.2f - 0.1f;
        p[i].vy = ((float)rand() / RAND_MAX) * 0.2f - 0.1f;
        p[i].vz = ((float)rand() / RAND_MAX) * 0.2f - 0.1f;
        p[i].mass = 1.0f + ((float)rand() / RAND_MAX) * 0.5f;
    }
}

// ---------------------------------------------------------------------------
int main(int argc, char **argv) {
    int N = 256;
    int steps = 10;
    float dt = 0.001f;
    float eps = SOFTENING;
    unsigned int seed = 42;

    for (int k = 1; k < argc; k++) {
        if (strcmp(argv[k], "--particles") == 0 && k+1 < argc) N = atoi(argv[++k]);
        else if (strcmp(argv[k], "--steps") == 0 && k+1 < argc) steps = atoi(argv[++k]);
        else if (strcmp(argv[k], "--dt") == 0 && k+1 < argc) dt = atof(argv[++k]);
        else if (strcmp(argv[k], "--seed") == 0 && k+1 < argc) seed = (unsigned int)atoi(argv[++k]);
    }

    Particle *particles = (Particle *)malloc(N * sizeof(Particle));
    Particle *cpu_particles = (Particle *)malloc(N * sizeof(Particle));
    float *cfx = (float *)malloc(N * sizeof(float));
    float *cfy = (float *)malloc(N * sizeof(float));
    float *cfz = (float *)malloc(N * sizeof(float));

    init_particles(particles, N, seed);
    memcpy(cpu_particles, particles, N * sizeof(Particle));

    // CPU reference simulation
    double e0_cpu = cpu_total_energy(cpu_particles, N, eps);
    for (int s = 0; s < steps; s++) {
        cpu_compute_forces(cpu_particles, cfx, cfy, cfz, N, eps);
        cpu_integrate(cpu_particles, cfx, cfy, cfz, N, dt);
    }
    double e1_cpu = cpu_total_energy(cpu_particles, N, eps);
    double cpu_energy_drift = fabs((e1_cpu - e0_cpu) / e0_cpu);

    // GPU simulation
    float *h_px = (float *)malloc(N * sizeof(float));
    float *h_py = (float *)malloc(N * sizeof(float));
    float *h_pz = (float *)malloc(N * sizeof(float));
    float *h_vx = (float *)malloc(N * sizeof(float));
    float *h_vy = (float *)malloc(N * sizeof(float));
    float *h_vz = (float *)malloc(N * sizeof(float));
    float *h_mass = (float *)malloc(N * sizeof(float));

    for (int i = 0; i < N; i++) {
        h_px[i] = particles[i].x;  h_py[i] = particles[i].y;  h_pz[i] = particles[i].z;
        h_vx[i] = particles[i].vx; h_vy[i] = particles[i].vy; h_vz[i] = particles[i].vz;
        h_mass[i] = particles[i].mass;
    }

    float *d_px, *d_py, *d_pz, *d_vx, *d_vy, *d_vz, *d_mass;
    float *d_fx, *d_fy, *d_fz, *d_acc_x, *d_acc_y, *d_acc_z;

    cudaMalloc(&d_px, N*sizeof(float)); cudaMalloc(&d_py, N*sizeof(float));
    cudaMalloc(&d_pz, N*sizeof(float)); cudaMalloc(&d_vx, N*sizeof(float));
    cudaMalloc(&d_vy, N*sizeof(float)); cudaMalloc(&d_vz, N*sizeof(float));
    cudaMalloc(&d_mass, N*sizeof(float));
    cudaMalloc(&d_fx, N*sizeof(float)); cudaMalloc(&d_fy, N*sizeof(float));
    cudaMalloc(&d_fz, N*sizeof(float));
    cudaMalloc(&d_acc_x, N*sizeof(float)); cudaMalloc(&d_acc_y, N*sizeof(float));
    cudaMalloc(&d_acc_z, N*sizeof(float));

    cudaMemcpy(d_px, h_px, N*sizeof(float), cudaMemcpyHostToDevice);
    cudaMemcpy(d_py, h_py, N*sizeof(float), cudaMemcpyHostToDevice);
    cudaMemcpy(d_pz, h_pz, N*sizeof(float), cudaMemcpyHostToDevice);
    cudaMemcpy(d_vx, h_vx, N*sizeof(float), cudaMemcpyHostToDevice);
    cudaMemcpy(d_vy, h_vy, N*sizeof(float), cudaMemcpyHostToDevice);
    cudaMemcpy(d_vz, h_vz, N*sizeof(float), cudaMemcpyHostToDevice);
    cudaMemcpy(d_mass, h_mass, N*sizeof(float), cudaMemcpyHostToDevice);

    for (int s = 0; s < steps; s++) {
        gpu_nbody_step(d_px, d_py, d_pz, d_vx, d_vy, d_vz, d_mass,
                       d_fx, d_fy, d_fz, d_acc_x, d_acc_y, d_acc_z, N, dt, eps);
    }
    cudaDeviceSynchronize();

    cudaMemcpy(h_px, d_px, N*sizeof(float), cudaMemcpyDeviceToHost);
    cudaMemcpy(h_py, d_py, N*sizeof(float), cudaMemcpyDeviceToHost);
    cudaMemcpy(h_pz, d_pz, N*sizeof(float), cudaMemcpyDeviceToHost);
    cudaMemcpy(h_vx, d_vx, N*sizeof(float), cudaMemcpyDeviceToHost);
    cudaMemcpy(h_vy, d_vy, N*sizeof(float), cudaMemcpyDeviceToHost);
    cudaMemcpy(h_vz, d_vz, N*sizeof(float), cudaMemcpyDeviceToHost);

    // Compute GPU energy
    Particle *gpu_final = (Particle *)malloc(N * sizeof(Particle));
    for (int i = 0; i < N; i++) {
        gpu_final[i].x = h_px[i]; gpu_final[i].y = h_py[i]; gpu_final[i].z = h_pz[i];
        gpu_final[i].vx = h_vx[i]; gpu_final[i].vy = h_vy[i]; gpu_final[i].vz = h_vz[i];
        gpu_final[i].mass = h_mass[i];
    }
    double e0_gpu_ref = cpu_total_energy(particles, N, eps);
    double e1_gpu = cpu_total_energy(gpu_final, N, eps);
    double gpu_energy_drift = fabs((e1_gpu - e0_gpu_ref) / e0_gpu_ref);

    // Max velocity
    float max_vel_gpu = 0.0f;
    float max_vel_cpu = 0.0f;
    for (int i = 0; i < N; i++) {
        float vg = sqrtf(h_vx[i]*h_vx[i] + h_vy[i]*h_vy[i] + h_vz[i]*h_vz[i]);
        float vc = sqrtf(cpu_particles[i].vx*cpu_particles[i].vx +
                         cpu_particles[i].vy*cpu_particles[i].vy +
                         cpu_particles[i].vz*cpu_particles[i].vz);
        if (vg > max_vel_gpu) max_vel_gpu = vg;
        if (vc > max_vel_cpu) max_vel_cpu = vc;
    }

    // Position error
    double pos_err = 0.0;
    for (int i = 0; i < N; i++) {
        double dx = h_px[i] - cpu_particles[i].x;
        double dy = h_py[i] - cpu_particles[i].y;
        double dz = h_pz[i] - cpu_particles[i].z;
        pos_err += sqrt(dx*dx + dy*dy + dz*dz);
    }
    pos_err /= N;

    printf("PARTICLES=%d\n", N);
    printf("STEPS=%d\n", steps);
    printf("CPU_ENERGY_DRIFT=%.6e\n", cpu_energy_drift);
    printf("GPU_ENERGY_DRIFT=%.6e\n", gpu_energy_drift);
    printf("MAX_VEL_CPU=%.4f\n", max_vel_cpu);
    printf("MAX_VEL_GPU=%.4f\n", max_vel_gpu);
    printf("AVG_POS_ERROR=%.6e\n", pos_err);
    printf("ENERGY_OK=%d\n", gpu_energy_drift < 0.01 ? 1 : 0);
    printf("VELOCITY_OK=%d\n", max_vel_gpu < 20.0f ? 1 : 0);
    printf("POSITION_OK=%d\n", pos_err < 0.01 ? 1 : 0);

    // Cleanup
    free(particles); free(cpu_particles); free(gpu_final);
    free(cfx); free(cfy); free(cfz);
    free(h_px); free(h_py); free(h_pz);
    free(h_vx); free(h_vy); free(h_vz); free(h_mass);
    cudaFree(d_px); cudaFree(d_py); cudaFree(d_pz);
    cudaFree(d_vx); cudaFree(d_vy); cudaFree(d_vz);
    cudaFree(d_mass); cudaFree(d_fx); cudaFree(d_fy); cudaFree(d_fz);
    cudaFree(d_acc_x); cudaFree(d_acc_y); cudaFree(d_acc_z);

    return 0;
}
