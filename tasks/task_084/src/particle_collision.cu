#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define BLOCK_SIZE 256
#define MAX_PARTICLES_PER_CELL 64
#define MAX_PAIRS 100000

// ---------------------------------------------------------------------------
// Particle system
// ---------------------------------------------------------------------------
typedef struct {
    float x, y, z;
    float vx, vy, vz;
} Particle;

// ---------------------------------------------------------------------------
// CPU reference brute-force collision detection (DO NOT MODIFY)
// ---------------------------------------------------------------------------
static float wrap_dist(float a, float b, float domain) {
    float d = a - b;
    if (d > domain * 0.5f) d -= domain;
    if (d < -domain * 0.5f) d += domain;
    return d;
}

int cpu_find_collisions(const Particle *particles, int N, float radius,
                         float domain_size, int *pairs, int max_pairs) {
    float r2 = radius * radius;
    int count = 0;
    for (int i = 0; i < N && count < max_pairs; i++) {
        for (int j = i + 1; j < N && count < max_pairs; j++) {
            float dx = wrap_dist(particles[i].x, particles[j].x, domain_size);
            float dy = wrap_dist(particles[i].y, particles[j].y, domain_size);
            float dz = wrap_dist(particles[i].z, particles[j].z, domain_size);
            float d2 = dx*dx + dy*dy + dz*dz;
            if (d2 <= r2) {
                pairs[count * 2]     = i;
                pairs[count * 2 + 1] = j;
                count++;
            }
        }
    }
    return count;
}

// ---------------------------------------------------------------------------
// GPU spatial hash collision detection — STUB (to be implemented)
// ---------------------------------------------------------------------------

// TODO: Implement spatial hash grid for collision detection.
//
// Approach:
//   1. Compute grid dimensions: grid_dim = ceil(domain_size / cell_size)
//      where cell_size = radius (so neighbors are within 1 cell distance).
//   2. Hash kernel: for each particle, compute cell (cx, cy, cz) from position,
//      atomicAdd to cell_count[hash], store particle index in cell_particles[hash][slot].
//   3. Collision kernel: for each particle i, compute its cell, iterate over
//      27 neighbor cells (including self). For each neighbor cell, iterate over
//      particles in that cell, compute distance with periodic wrapping.
//      If distance <= radius and j > i, record pair.
//   4. Handle cell overflow: if cell_count > MAX_PARTICLES_PER_CELL, clamp.
//   5. Handle wrapping: neighbor cell indices wrap around (mod grid_dim).
//
// Output pairs as (i, j) with i < j, no duplicates.

int gpu_spatial_hash_collisions(const Particle *h_particles, int N,
                                 float radius, float domain_size,
                                 int *h_pairs, int max_pairs,
                                 int *overflow_count) {
    // STUB: returns 0 collisions
    *overflow_count = 0;
    return 0;
}

// ---------------------------------------------------------------------------
// Initialization
// ---------------------------------------------------------------------------
void init_particles(Particle *p, int N, float domain_size, unsigned int seed) {
    srand(seed);
    for (int i = 0; i < N; i++) {
        p[i].x = ((float)rand() / RAND_MAX) * domain_size;
        p[i].y = ((float)rand() / RAND_MAX) * domain_size;
        p[i].z = ((float)rand() / RAND_MAX) * domain_size;
        p[i].vx = ((float)rand() / RAND_MAX) * 2.0f - 1.0f;
        p[i].vy = ((float)rand() / RAND_MAX) * 2.0f - 1.0f;
        p[i].vz = ((float)rand() / RAND_MAX) * 2.0f - 1.0f;
    }
}

// Place some particles at boundaries to test wrapping
void add_boundary_particles(Particle *p, int start, int count, float domain_size) {
    float eps = 0.01f;
    for (int i = 0; i < count && start + i < count + start; i++) {
        int idx = start + i;
        // Alternate between near-zero and near-domain_size positions
        if (i % 2 == 0) {
            p[idx].x = eps;
            p[idx].y = ((float)rand() / RAND_MAX) * domain_size;
            p[idx].z = ((float)rand() / RAND_MAX) * domain_size;
        } else {
            p[idx].x = domain_size - eps;
            p[idx].y = p[idx-1].y;  // Same y,z as partner — should collide across boundary
            p[idx].z = p[idx-1].z;
        }
        p[idx].vx = p[idx].vy = p[idx].vz = 0.0f;
    }
}

// ---------------------------------------------------------------------------
int main(int argc, char **argv) {
    int N = 200;
    float radius = 2.0f;
    float domain_size = 50.0f;
    unsigned int seed = 42;
    int boundary_test = 0;

    for (int k = 1; k < argc; k++) {
        if (strcmp(argv[k], "--particles") == 0 && k+1 < argc) N = atoi(argv[++k]);
        else if (strcmp(argv[k], "--radius") == 0 && k+1 < argc) radius = atof(argv[++k]);
        else if (strcmp(argv[k], "--domain") == 0 && k+1 < argc) domain_size = atof(argv[++k]);
        else if (strcmp(argv[k], "--seed") == 0 && k+1 < argc) seed = (unsigned int)atoi(argv[++k]);
        else if (strcmp(argv[k], "--boundary") == 0) boundary_test = 1;
    }

    Particle *particles = (Particle *)malloc(N * sizeof(Particle));
    init_particles(particles, N, domain_size, seed);

    if (boundary_test && N >= 20) {
        add_boundary_particles(particles, N - 20, 20, domain_size);
    }

    int *cpu_pairs = (int *)malloc(MAX_PAIRS * 2 * sizeof(int));
    int *gpu_pairs = (int *)malloc(MAX_PAIRS * 2 * sizeof(int));

    int cpu_count = cpu_find_collisions(particles, N, radius, domain_size,
                                         cpu_pairs, MAX_PAIRS);
    int overflow = 0;
    int gpu_count = gpu_spatial_hash_collisions(particles, N, radius, domain_size,
                                                 gpu_pairs, MAX_PAIRS, &overflow);

    // Check: all CPU pairs must be found in GPU results (no false negatives)
    int false_negatives = 0;
    for (int c = 0; c < cpu_count; c++) {
        int ci = cpu_pairs[c * 2];
        int cj = cpu_pairs[c * 2 + 1];
        int found = 0;
        for (int g = 0; g < gpu_count; g++) {
            int gi = gpu_pairs[g * 2];
            int gj = gpu_pairs[g * 2 + 1];
            if ((gi == ci && gj == cj) || (gi == cj && gj == ci)) {
                found = 1;
                break;
            }
        }
        if (!found) false_negatives++;
    }

    // Check for duplicates in GPU output
    int duplicates = 0;
    for (int g = 0; g < gpu_count; g++) {
        for (int h = g + 1; h < gpu_count; h++) {
            int gi = gpu_pairs[g * 2], gj = gpu_pairs[g * 2 + 1];
            int hi = gpu_pairs[h * 2], hj = gpu_pairs[h * 2 + 1];
            if ((gi == hi && gj == hj) || (gi == hj && gj == hi)) {
                duplicates++;
            }
        }
    }

    // Check ordering (i < j)
    int ordering_ok = 1;
    for (int g = 0; g < gpu_count; g++) {
        if (gpu_pairs[g * 2] >= gpu_pairs[g * 2 + 1]) {
            ordering_ok = 0;
            break;
        }
    }

    printf("PARTICLES=%d\n", N);
    printf("RADIUS=%.2f\n", radius);
    printf("DOMAIN=%.2f\n", domain_size);
    printf("CPU_COLLISIONS=%d\n", cpu_count);
    printf("GPU_COLLISIONS=%d\n", gpu_count);
    printf("FALSE_NEGATIVES=%d\n", false_negatives);
    printf("DUPLICATES=%d\n", duplicates);
    printf("ORDERING_OK=%d\n", ordering_ok);
    printf("OVERFLOW=%d\n", overflow);
    printf("BOUNDARY_TEST=%d\n", boundary_test);
    printf("MATCH=%d\n",
        (false_negatives == 0 && duplicates == 0 && ordering_ok &&
         gpu_count >= cpu_count) ? 1 : 0);

    free(particles); free(cpu_pairs); free(gpu_pairs);
    return 0;
}
